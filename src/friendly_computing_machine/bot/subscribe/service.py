import asyncio
import logging
from typing import Optional

from amqpstorm import Connection

from external.manman_status_api.api.default_api import DefaultApi as ManManStatusAPI
from friendly_computing_machine.bot.app import SlackWebClientFCM

logger = logging.getLogger(__name__)


class ManManSubscribeService:
    """
    ManMan Subscribe Service - handles events from RabbitMQ topics and sends
    notifications to Slack based on worker and instance status changes.

    This service subscribes to manman topics for:
    - Worker lifecycle events (start, running, lost, complete)
    - Instance lifecycle events (start, init, running, lost, complete)

    Events are processed to:
    - Send formatted Slack messages with action buttons
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

        # hardcoding this for now, sue me
        self._worker_status_queue = f"fcm-{self._app_env}.manman.worker.status"
        self._instance_status_queue = f"fcm-{self._app_env}.manman.server.status"

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

        # TODO - set up RabbitMQ subscriptions

        self._channel.queue.declare(queue=self._worker_status_queue, durable=True)
        self._channel.queue.declare(queue=self._instance_status_queue, durable=True)

        # hardcoding, sue me
        self._channel.queue.bind(
            exchange="external",
            queue=self._worker_status_queue,
            routing_key="external.status.worker-instance.*",
        )
        self._channel.queue.bind(
            exchange="external",
            queue=self._instance_status_queue,
            routing_key="external.status.game-server-instance.*",
        )

        try:
            while self._is_running:
                # TODO: Implement message consumption from RabbitMQ
                # TODO: Process worker status updates
                # TODO: Process instance status updates
                # TODO: Send Slack notifications
                await self._process_pending_messages()

                await asyncio.sleep(0.25)
        except Exception as e:
            logger.error(f"Error in subscribe service: {e}")
            raise

    async def stop(self):
        """Stop the subscribe service gracefully."""
        logger.info("Stopping ManMan Subscribe Service")
        self._is_running = False

    async def _process_pending_messages(self):
        """Process any pending messages from the queues."""
        logger.debug("Processing messages (stub)")
        # fetch messages from RabbitMQ queues

    def _handle_worker_status_update(self, worker_id: str, status: str, metadata: dict):
        """
        Handle worker status update events.

        Args:
            worker_id: ID of the worker
            status: New status (start, running, lost, crashed, complete)
            metadata: Additional event metadata
        """
        logger.info(f"Worker {worker_id} status update: {status}")
        # TODO: Implement worker status handling
        # TODO: Send appropriate Slack message with buttons
        # TODO: Update database status

    def _handle_instance_status_update(
        self, instance_id: str, status: str, metadata: dict
    ):
        """
        Handle instance status update events.

        Args:
            instance_id: ID of the game server instance
            status: New status (start, init, running, lost, crashed, complete)
            metadata: Additional event metadata
        """
        logger.info(f"Instance {instance_id} status update: {status}")
        # TODO: Implement instance status handling
        # TODO: Send appropriate Slack message with action buttons
        # TODO: Update database status

    def _send_slack_notification(
        self, channel: str, message: str, blocks: Optional[list] = None
    ):
        """
        Send a notification to Slack.

        Args:
            channel: Slack channel to send to
            message: Text message
            blocks: Optional Slack block kit format for rich messages
        """
        logger.info(f"Sending Slack notification to {channel}: {message}")
        # TODO: Implement Slack Web API integration
        # TODO: Send message with blocks for action buttons
