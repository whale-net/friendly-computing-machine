import asyncio
import functools  # Added
import json
import logging
from dataclasses import dataclass
from typing import Callable, Optional

from amqpstorm import Connection

from external.manman_status_api.api.default_api import DefaultApi as ManManStatusAPI
from external.manman_status_api.models.status_info import StatusInfo
from friendly_computing_machine.bot.app import SlackWebClientFCM

logger = logging.getLogger(__name__)


@dataclass
class QueueConfig:
    """Configuration for a message queue."""

    name: str
    routing_key: str
    handler: Callable[[StatusInfo], None]

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Queue name cannot be empty")
        if not self.routing_key:
            raise ValueError("Routing key cannot be empty")
        if not callable(self.handler):
            raise ValueError("Handler must be callable")


class ManManSubscribeService:
    """
    ManMan Subscribe Service - handles events from RabbitMQ topics and sends
    notifications to Slack based on worker and instance status changes.

    This service subscribes to manman topics for:
    - Worker lifecycle events (start, running, lost, complete)
    - Instance lifecycle events (start, init, running, lost, complete)

    Events are processed to:
    - Send formatted Slack messages with action buttons

    CONTROL FLOW (Consume-based):
    1. Initialization (__init__):
       - Sets up RabbitMQ connection, channel, and queue configs.
       - Initializes internal loop and consumer task references.

    2. Service Start (start()):
       - Declares durable queues and binds them to the exchange (using asyncio.to_thread).
       - Registers consumers for each queue using `channel.basic.consume`.
         The callback (`_amqp_message_callback`) is set for each consumer.
       - Starts `channel.start_consuming()` in a background asyncio task.
         This task blocks internally, listening for messages.

    3. Message Arrival & Callback (`_amqp_message_callback`):
       - Called by AMQPStorm's I/O thread when a message arrives.
       - Parses the message body (JSON).
       - Schedules `_process_consumed_message` on the main asyncio event loop
         using `asyncio.run_coroutine_threadsafe`.
       - Handles initial parsing errors and schedules message rejection if needed.

    4. Async Message Processing (`_process_consumed_message`):
       - Runs on the asyncio event loop.
       - Deserializes message data to `StatusInfo`.
       - Calls the configured handler via `_handle_status_info_async`.
       - Acknowledges (ack) or rejects (nack) the message on the channel
         using `asyncio.to_thread`.

    5. Handler Execution (`_handle_status_info_async`):
       - Wraps synchronous handlers (e.g., `_handle_worker_status_update`)
         in `loop.run_in_executor()` to prevent blocking the event loop.

    6. Service Stop (stop()):
       - Signals `channel.stop_consuming()` (via asyncio.to_thread).
       - Waits for the background consumer task to finish.
       - Closes the AMQP channel.
    """

    def __init__(
        self,
        app_env: str,
        rabbitmq_connection: Connection,
        slack_api: SlackWebClientFCM,
        manman_status_api: ManManStatusAPI,
    ):
        """
        Initialize the ManMan Subscribe Service.

        Args:
            rabbitmq_connection: Connection object for RabbitMQ
            slack_api: SlackWebClientFCM for Slack interactions
            manman_status_api: ManManStatusAPI for status interactions
            app_env: Application environment string
        """
        self._rabbitmq_connection = rabbitmq_connection
        self._channel = rabbitmq_connection.channel()
        self._slack_api = slack_api
        self._is_running = False
        self._manman_status_api = manman_status_api
        self._app_env = app_env

        self._loop: asyncio.AbstractEventLoop | None = None  # Added
        self._consumer_bg_task: asyncio.Task | None = None  # Added

        # Queue configuration using proper classes
        self._queues = {
            "worker": QueueConfig(
                name=f"fcm-{self._app_env}.manman.worker.status",
                routing_key="external.status.worker-instance.*",
                handler=self._handle_worker_status_update,
            ),
            "instance": QueueConfig(
                name=f"fcm-{self._app_env}.manman.server.status",
                routing_key="external.status.game-server-instance.*",
                handler=self._handle_instance_status_update,
            ),
        }

        logger.info("ManMan Subscribe Service initialized")

    async def start(self):
        """
        Start the subscribe service in consume mode.
        Declares queues, sets up consumers, and starts message consumption in a background task.
        """
        logger.info("Starting ManMan Subscribe Service (Consume Mode)")
        if self._is_running:
            logger.warning("Service is already running.")
            return

        self._is_running = True
        self._loop = asyncio.get_running_loop()

        try:
            # Set up queues and bindings
            for queue_type, config in self._queues.items():
                logger.info(f"Declaring and binding queue: {config.name}")
                await asyncio.to_thread(
                    self._channel.queue.declare, queue=config.name, durable=True
                )
                await asyncio.to_thread(
                    self._channel.queue.bind,
                    exchange="external",
                    queue=config.name,
                    routing_key=config.routing_key,
                )
                logger.info(f"Configured {queue_type} queue: {config.name}")

                # Register consumer for this queue
                bound_callback = functools.partial(
                    self._amqp_message_callback, queue_config=config
                )
                await asyncio.to_thread(
                    self._channel.basic.consume,
                    callback=bound_callback,
                    queue=config.name,
                    no_ack=False,  # Manual acknowledgment
                )
                logger.info(f"Consumer set up for queue: {config.name}")

            logger.info("Starting AMQPStorm message consumption background task...")
            self._consumer_bg_task = self._loop.create_task(
                asyncio.to_thread(self._channel.start_consuming),
                name="amqp_consumer_thread",
            )
            logger.info("ManMan Subscribe Service started successfully.")

        except Exception as e:
            logger.error(f"Failed to start ManMan Subscribe Service: {e}")
            self._is_running = False
            if self._consumer_bg_task and not self._consumer_bg_task.done():
                self._consumer_bg_task.cancel()
            # Re-raise the exception to signal failure
            raise

    async def stop(self):
        """
        Stop the subscribe service gracefully.
        Signals the AMQP consumer to stop, waits for it, and closes the channel.
        """
        logger.info("Stopping ManMan Subscribe Service (Consume Mode)")
        if not self._is_running and not (
            self._consumer_bg_task and not self._consumer_bg_task.done()
        ):
            logger.info("Service not running or already stopped/stopping.")
            return

        # Signal that the service is stopping
        self._is_running = False

        if self._channel and self._channel.is_open:
            logger.info("Requesting AMQP consumer to stop...")
            try:
                # This call makes start_consuming() return in its thread.
                await asyncio.to_thread(self._channel.stop_consuming)
                logger.info("AMQP consumer stop request sent.")
            except Exception as e:
                logger.error(f"Error requesting AMQP consumer to stop: {e}")
        else:
            logger.info("Channel not available or not open for stopping consumers.")

        if self._consumer_bg_task:
            logger.info("Waiting for consumer background task to complete...")
            try:
                await asyncio.wait_for(self._consumer_bg_task, timeout=10.0)
                logger.info("Consumer background task completed.")
            except asyncio.TimeoutError:
                logger.warning(
                    "Timeout waiting for consumer background task. Attempting to cancel."
                )
                self._consumer_bg_task.cancel()
                try:
                    await self._consumer_bg_task  # Allow cancellation to propagate
                except asyncio.CancelledError:
                    logger.info("Consumer background task was cancelled.")
                except Exception as e:
                    logger.error(f"Error during consumer task cancellation: {e}")
            except Exception as e:
                logger.error(f"Error waiting for consumer background task: {e}")
            finally:
                self._consumer_bg_task = None

        if self._channel and self._channel.is_open:
            logger.info("Closing AMQP channel.")
            try:
                await asyncio.to_thread(self._channel.close)
                logger.info("AMQP channel closed.")
            except Exception as e:
                logger.error(f"Error closing AMQP channel: {e}")
        self._channel = None  # Mark as closed

        logger.info("ManMan Subscribe Service stopped.")

    def _amqp_message_callback(self, message, queue_config: QueueConfig):
        """
        Synchronous callback executed by AMQPStorm's I/O thread when a message is received.
        Parses the message and schedules asynchronous processing on the asyncio event loop.
        """
        if not self._loop:  # Should be set by start()
            logger.error(
                "Event loop not available in AMQP callback. Cannot process message."
            )
            # Potentially try to reject if channel is available, but this is a bad state.
            return

        logger.info(
            f"Received message on queue {queue_config.name}: {message.body[:100]}..."
        )
        try:
            message_data = json.loads(message.body)
            # Schedule the async processing on the asyncio event loop
            asyncio.run_coroutine_threadsafe(
                self._process_consumed_message(
                    message_data, queue_config, message.delivery_tag
                ),
                self._loop,
            )
        except json.JSONDecodeError:
            logger.warning(
                f"Message on {queue_config.name} (delivery_tag: {message.delivery_tag}) is not valid JSON, scheduling rejection: {message.body}"
            )

            async def reject_invalid_json():
                try:
                    await asyncio.to_thread(
                        self._channel.basic.reject,
                        delivery_tag=message.delivery_tag,
                        requeue=False,
                    )
                    logger.info(
                        f"Message {message.delivery_tag} rejected (invalid JSON)."
                    )
                except Exception as e_reject:
                    logger.error(
                        f"Async rejection failed for {message.delivery_tag} (invalid JSON): {e_reject}"
                    )

            asyncio.run_coroutine_threadsafe(reject_invalid_json(), self._loop)
        except Exception as e:
            logger.error(
                f"Error in AMQP callback for {queue_config.name} (delivery_tag: {message.delivery_tag}): {e}, scheduling rejection."
            )

            async def reject_on_error():
                try:
                    await asyncio.to_thread(
                        self._channel.basic.reject,
                        delivery_tag=message.delivery_tag,
                        requeue=False,
                    )
                    logger.info(
                        f"Message {message.delivery_tag} rejected (callback error)."
                    )
                except Exception as e_reject:
                    logger.error(
                        f"Async rejection failed for {message.delivery_tag} (callback error): {e_reject}"
                    )

            asyncio.run_coroutine_threadsafe(reject_on_error(), self._loop)

    async def _process_consumed_message(
        self, message_data: dict, queue_config: QueueConfig, delivery_tag: int
    ):
        """
        Asynchronously processes a consumed message.
        Deserializes, calls the handler, and acknowledges/rejects the message.
        Runs in the asyncio event loop.
        """
        logger.info(
            f"Async processing message from {queue_config.name} (delivery_tag: {delivery_tag})"
        )
        try:
            status_info = StatusInfo.from_dict(message_data)
            await self._handle_status_info_async(queue_config.handler, status_info)
            await asyncio.to_thread(self._channel.basic.ack, delivery_tag=delivery_tag)
            logger.debug(
                f"Message from {queue_config.name} (delivery_tag: {delivery_tag}) acknowledged."
            )
        except Exception as e:
            logger.error(
                f"Error processing consumed message from {queue_config.name} (delivery_tag: {delivery_tag}): {e}"
            )
            try:
                await asyncio.to_thread(
                    self._channel.basic.reject, delivery_tag=delivery_tag, requeue=False
                )
                logger.warning(
                    f"Message from {queue_config.name} (delivery_tag: {delivery_tag}) rejected due to processing error."
                )
            except Exception as e_reject:
                logger.error(
                    f"Failed to reject message from {queue_config.name} (delivery_tag: {delivery_tag}) after processing error: {e_reject}"
                )

    async def _handle_status_info_async(
        self, handler: Callable[[StatusInfo], None], status_info: StatusInfo
    ):
        """
        Generic async status info handler wrapper.

        Args:
            handler: The sync handler function to call
            status_info: Parsed StatusInfo object
        """
        try:
            logger.info(f"Processing status update for {status_info}")

            # Run handler in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, handler, status_info)

        except Exception as e:
            logger.error(f"Error handling status info: {e}")

    def _handle_worker_status_update(self, status_info: StatusInfo):
        """
        Handle worker status update events.

        Args:
            status_info: StatusInfo object containing worker status information
        """
        logger.info(
            f"Worker {status_info.worker_id} status update: {status_info.status}"
        )
        # TODO: Implement worker status handling
        # TODO: Send appropriate Slack message with buttons
        # TODO: Update database status

    def _handle_instance_status_update(self, status_info: StatusInfo):
        """
        Handle instance status update events.

        Args:
            status_info: StatusInfo object containing instance status information
        """
        logger.info(
            f"Instance {status_info.game_server_instance_id} status update: {status_info.status}"
        )
        # TODO: Implement instance status handling
        # TODO: Send appropriate Slack message with action buttons
        # TODO: Update database status

    async def _send_slack_notification(
        self, channel: str, message: str, blocks: Optional[list] = None
    ):
        """
        Send a notification to Slack asynchronously.

        Args:
            channel: Slack channel to send to
            message: Text message
            blocks: Optional Slack block kit format for rich messages
        """
        logger.info(f"Sending Slack notification to {channel}: {message}")
        # TODO: Implement Slack Web API integration
        # TODO: Send message with blocks for action buttons
        # For now, just log the notification
        await asyncio.sleep(0.01)  # Placeholder for async Slack API call
