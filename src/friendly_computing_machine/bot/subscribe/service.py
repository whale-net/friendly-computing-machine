import asyncio
import functools  # Added
import json
import logging
from dataclasses import dataclass
from typing import Callable

from amqpstorm import Connection

from external.manman_status_api.api.default_api import DefaultApi as ManManStatusAPI
from external.manman_status_api.models.status_info import StatusInfo
from external.manman_status_api.models.status_type import StatusType
from friendly_computing_machine.bot.app import SlackWebClientFCM
from friendly_computing_machine.bot.util import slack_send_message
from friendly_computing_machine.db.dal import (
    get_manman_status_update_from_create,
    get_slack_special_channel_type_from_name,
    get_slack_special_channels_from_type,
    insert_manman_status_update,
    update_manman_status_update,
)
from friendly_computing_machine.models.manman import (
    ManManStatusUpdateCreate,
)

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

        # Hardcoding for now
        self._manman_channel_type = get_slack_special_channel_type_from_name(
            "manman_dev"
        )
        if self._manman_channel_type:
            self._manman_channels = get_slack_special_channels_from_type(
                self._manman_channel_type
            )
        else:
            logger.warning(
                "No ManMan channel type found, using default channel for notifications."
            )
            self._manman_channels = []

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
        Extracts necessary data and schedules the full asynchronous processing on the event loop.
        """
        if not self._loop:  # Should be set by start()
            logger.error(
                "Event loop not available in AMQP callback. Cannot process message."
            )
            # Cannot safely reject here without the loop or a valid channel reference strategy
            # for this specific scenario. This indicates a severe setup issue.
            return

        try:
            # Extract all necessary information from the message object here,
            # as the message object itself might not be safe to pass across threads
            # or its lifetime might be tied to the callback's scope in some libraries.
            body = message.body
            delivery_tag = message.delivery_tag
        except Exception as e:
            logger.error(
                f"Error accessing message properties in AMQP callback for queue {queue_config.name}: {e}"
            )
            # Cannot process further if basic message properties are inaccessible.
            return

        logger.info(
            f"Received message on queue {queue_config.name} (delivery_tag: {delivery_tag}), scheduling for async processing."
        )
        asyncio.run_coroutine_threadsafe(
            self._process_message_async(body, delivery_tag, queue_config), self._loop
        )

    async def _process_message_async(
        self, body: bytes, delivery_tag: int, queue_config: QueueConfig
    ):
        """
        Asynchronously parses, processes, and acknowledges/rejects a message.
        This method runs in the asyncio event loop.
        """
        logger.info(
            f"Async processing message from {queue_config.name} (delivery_tag: {delivery_tag})"
        )
        try:
            message_data = json.loads(body)
            logger.debug(f"Message JSON parsed for {delivery_tag}: {message_data}")

            status_info = StatusInfo.from_dict(message_data)
            logger.debug(f"StatusInfo deserialized for {delivery_tag}: {status_info}")

            await self._handle_status_info_async(queue_config.handler, status_info)

            logger.debug(
                f"Attempting to ACK message {delivery_tag} on queue {queue_config.name}."
            )
            if self._channel and self._channel.is_open:  # Ensure channel is usable
                await asyncio.to_thread(
                    self._channel.basic.ack, delivery_tag=delivery_tag
                )
                logger.info(
                    f"Message {delivery_tag} from {queue_config.name} acknowledged."
                )
            else:
                logger.warning(
                    f"Channel not available or closed, cannot ACK message {delivery_tag} from {queue_config.name}."
                )
                # This message will likely be redelivered by RabbitMQ after visibility timeout.

        except json.JSONDecodeError as e:
            logger.warning(
                f"Invalid JSON in message from {queue_config.name} (delivery_tag: {delivery_tag}): {e}. Body: {body[:200]}"
            )
            if self._channel and self._channel.is_open:
                await asyncio.to_thread(
                    self._channel.basic.reject, delivery_tag=delivery_tag, requeue=False
                )
                logger.info(f"Message {delivery_tag} (invalid JSON) rejected.")
            else:
                logger.warning(
                    f"Channel not available or closed, cannot REJECT (invalid JSON) message {delivery_tag}."
                )
        except Exception as e:
            logger.error(
                f"Error processing message from {queue_config.name} (delivery_tag: {delivery_tag}): {e}",
                exc_info=True,
            )
            if self._channel and self._channel.is_open:
                await asyncio.to_thread(
                    self._channel.basic.reject, delivery_tag=delivery_tag, requeue=False
                )
                logger.warning(
                    f"Message {delivery_tag} rejected due to processing error."
                )
            else:
                logger.warning(
                    f"Channel not available or closed, cannot REJECT (processing error) message {delivery_tag}."
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
            f"Worker {status_info.worker_id} status update: {status_info.status_info_id}"
        )

        # TODO: temporal workflow
        # create a workflow for each worker/server instance by-id
        # when a worker/server instance is created, start a workflow
        # when a worker/server instance is updated, send a signal to the workflow
        # the workflow should handle the status updates and slack logic
        # this will be the synchronization point for updates hopefully.
        # can also keep track of event timestamp and make sure that we don't ever go from a current state to an older state
        # however, for now I am just going to write to the database and send slack messages
        # the database will ultimately be the source of truth regardless of implementation
        # however, the control flow around it will be different
        # TODO - write to database
        # TODO - if new -> send slack message
        # TODO - if exists -> update slack message
        # TODO - always retrieve info in paralell (? what is this requirement mean? just temporal note?)
        # from friendly_computing_machine.bot.util import slack_send_message

        status_update_create = ManManStatusUpdateCreate.from_status_info(status_info)
        if status_info.status_type == StatusType.CREATED:
            # If the worker is initializing, we create a new status update
            up = insert_manman_status_update(status_update_create)
            logger.info(
                "Created new ManMan status update for initializing worker %s", up.id
            )
        elif status_info.status_type in (
            StatusType.RUNNING,
            StatusType.LOST,
        ):
            # TODO START HERE 5/28 - the timing is needed to allow the above update to insert. perhaps need retry for now
            # will see how temporla hnales this
            import time

            time.sleep(2)

            status_update = get_manman_status_update_from_create(status_update_create)
            slack_send_message()
            logger.info("TODO send slack message update")
            status_update.current_status = status_info.status_type.value
            update_manman_status_update(status_update)
        elif status_info.status_type == StatusType.COMPLETE:
            status_update = get_manman_status_update_from_create(status_update_create)
            status_update.current_status = status_info.status_type.value
            logger.info("TODO send slack message update")
            update_manman_status_update(status_update)
        else:
            # includes Initializing, which is not handled here, but is for server
            raise ValueError(
                f"Unhandled worker status type for worker: {status_info.status_type}"
            )
        logger.info(
            f"Worker {status_info.worker_id} status update processed: {status_info.status_info_id}"
        )

    def _handle_instance_status_update(self, status_info: StatusInfo):
        """
        Handle instance status update events.

        Args:
            status_info: StatusInfo object containing instance status information
        """
        logger.info(
            f"Instance {status_info.game_server_instance_id} status update: {status_info.status_info_id}"
        )
        # TODO: Implement instance status handling
        # TODO: Send appropriate Slack message with action buttons
        # TODO: Update database status

    async def _send_slack_notification(
        self,
    ):
        for channel in self._manman_channels:
            try:
                logger.info(f"Sent Slack notification to channel {channel}")
            except Exception as e:
                logger.error(
                    f"Failed to send Slack notification to channel {channel}: {e}"
                )
