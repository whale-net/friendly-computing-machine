import asyncio
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

    CONTROL FLOW:
    1. Initialization (__init__):
       - Sets up RabbitMQ connection and channel and queue configs

    2. Service Start (start()):
       - Declares durable queues in RabbitMQ
       - Binds queues to exchange with routing keys

    3. Message Processing Loop:
       - _process_all_queues() runs all queue processors concurrently using asyncio.gather()
       - _process_queue() polls each queue using basic_get() (non-blocking)
       - If message found: deserializes JSON → StatusInfo object → calls configured handler
       - Messages are acknowledged after successful processing

    4. Handler Execution:
       - _handle_status_info_async() wraps sync handlers in run_in_executor()
       - Worker messages → _handle_worker_status_update()
       - Instance messages → _handle_instance_status_update()
       - Handlers receive typed StatusInfo objects with all message data
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
            slack_bot_token: Slack Bot Token for Web API calls (sending messages)
        """
        self._rabbitmq_connection = rabbitmq_connection
        self._channel = rabbitmq_connection.channel()
        self._slack_api = slack_api
        self._is_running = False
        self._manman_status_api = manman_status_api
        self._app_env = app_env

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
        Start the subscribe service.

        This will:
        1. Set up topic subscriptions for worker and instance events
        2. Begin processing messages
        """
        logger.info("Starting ManMan Subscribe Service")
        self._is_running = True

        # Set up queues and bindings
        for queue_type, config in self._queues.items():
            self._channel.queue.declare(queue=config.name, durable=True)
            self._channel.queue.bind(
                exchange="external",
                queue=config.name,
                routing_key=config.routing_key,
            )
            logger.info(f"Configured {queue_type} queue: {config.name}")

        try:
            while self._is_running:
                # Process all queues concurrently
                await self._process_all_queues()

                # Simple fixed sleep interval
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in subscribe service: {e}")
            raise

    async def stop(self):
        """Stop the subscribe service gracefully."""
        logger.info("Stopping ManMan Subscribe Service")
        self._is_running = False

    async def _process_all_queues(self):
        """Process all configured queues concurrently."""
        logger.debug("Processing all queues")

        # Create tasks for all queues
        tasks = [
            self._process_queue(queue_type, config)
            for queue_type, config in self._queues.items()
        ]

        # Process all queues concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_queue(self, queue_type: str, config: QueueConfig):
        """
        Generic queue processor for any queue type.

        Args:
            queue_type: Type of queue (e.g., "worker", "instance")
            config: Queue configuration object
        """
        try:
            message = self._channel.basic.get(queue=config.name, no_ack=False)
            if not message:
                return

            logger.info(f"Received {queue_type} message: {message.body}")
            print(f"{queue_type.title()} message content: {message.body}")

            # Parse and process message
            try:
                message_data = json.loads(message.body)
                print(
                    f"{queue_type.title()} message parsed: {json.dumps(message_data, indent=2)}"
                )

                # Deserialize to StatusInfo and call the configured handler
                status_info = StatusInfo.from_dict(message_data)
                await self._handle_status_info_async(config.handler, status_info)

            except json.JSONDecodeError:
                print(f"{queue_type.title()} message (not JSON): {message.body}")
                logger.warning(
                    f"{queue_type} message is not valid JSON, skipping processing"
                )
            except Exception as e:
                logger.error(f"Error processing {queue_type} message: {e}")

            message.ack()

        except Exception as e:
            logger.warning(f"Error processing {queue_type} messages: {e}")

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
