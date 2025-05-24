import asyncio
import logging

from friendly_computing_machine.bot.subscribe.service import ManManSubscribeService
from friendly_computing_machine.health import run_health_server
from friendly_computing_machine.util import NamedThreadPool

logger = logging.getLogger(__name__)


def run_manman_subscribe(rabbitmq_url: str, slack_bot_token: str):
    """
    Run the ManMan Subscribe Service.

    This starts the service that listens to RabbitMQ topics for manman events
    and sends notifications to Slack.

    Args:
        rabbitmq_url: URL for RabbitMQ connection
        slack_bot_token: Slack Bot Token for Web API calls (sending messages)
    """
    logger.info("Starting ManMan Subscribe Service")

    async def run_service():
        service = ManManSubscribeService(rabbitmq_url, slack_bot_token)
        try:
            await service.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await service.stop()
        except Exception as e:
            logger.error(f"Service error: {e}")
            await service.stop()
            raise

    # Run the service with health server in a thread pool
    with NamedThreadPool() as executor:
        # Start the health server in a separate thread
        executor.submit(run_health_server, thread_name="health")

        # Run the main subscribe service
        try:
            asyncio.run(run_service())
        except KeyboardInterrupt:
            logger.info("Service interrupted")
        except Exception as e:
            logger.error(f"Service failed: {e}")
            raise

        logger.info("ManMan Subscribe Service stopped")
