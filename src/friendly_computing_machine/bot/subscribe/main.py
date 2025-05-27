import asyncio
import logging

from friendly_computing_machine.bot.app import get_slack_web_client
from friendly_computing_machine.bot.subscribe.service import ManManSubscribeService
from friendly_computing_machine.manman.api import ManManStatusAPI
from friendly_computing_machine.rabbitmq.util import (
    get_rabbitmq_connection,
)

logger = logging.getLogger(__name__)


def run_manman_subscribe(app_env: str):
    """
    Run the ManMan Subscribe Service.

    This starts the service that listens to RabbitMQ topics for manman events
    and sends notifications to Slack.

    Args:
        slack_bot_token: Slack Bot Token for Web API calls (sending messages)
    """
    logger.info("Starting ManMan Subscribe Service")

    rabbit_mq_connection = get_rabbitmq_connection()
    slack_api = get_slack_web_client()
    manman_status_api = ManManStatusAPI.get_api()

    async def run_service():
        service = ManManSubscribeService(
            app_env, rabbit_mq_connection, slack_api, manman_status_api
        )
        try:
            await service.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await service.stop()
        except Exception as e:
            logger.error(f"Service error: {e}")
            await service.stop()
            raise

    # Run the main subscribe service
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("Service interrupted")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        raise

    logger.info("ManMan Subscribe Service stopped")
