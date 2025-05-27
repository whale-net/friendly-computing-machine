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
        app_env: Application environment string
    """
    logger.info("Starting ManMan Subscribe Service")

    rabbit_mq_connection = get_rabbitmq_connection()
    slack_api = get_slack_web_client()
    manman_status_api = ManManStatusAPI.get_api()

    async def run_service_async_logic():
        service = ManManSubscribeService(
            app_env, rabbit_mq_connection, slack_api, manman_status_api
        )
        try:
            await service.start()
            if service._consumer_bg_task:
                logger.info("ManMan Subscribe Service running, awaiting consumer task.")
                await (
                    service._consumer_bg_task
                )  # Wait for the consumer task to complete or be cancelled
            else:
                # This should not happen if service.start() is implemented correctly
                logger.error(
                    "Consumer background task (_consumer_bg_task) was not created. Service cannot run."
                )
        except asyncio.CancelledError:
            logger.info(
                "Service's main async task was cancelled (e.g., by KeyboardInterrupt)."
            )
            # The finally block will handle stopping the service.
        except Exception as e:
            logger.error(
                f"Unhandled exception in service's main async task: {e}", exc_info=True
            )
            raise  # Re-raise to allow outer try/except to catch it
        finally:
            # This block executes on normal completion of _consumer_bg_task,
            # cancellation, or if an unhandled exception occurred in the try block.
            if "service" in locals() and service:  # Ensure service was instantiated
                logger.info(
                    "Main async task is ending. Ensuring ManManSubscribeService is stopped."
                )
                await service.stop()

    # Run the main subscribe service
    try:
        asyncio.run(run_service_async_logic())
    except KeyboardInterrupt:
        # asyncio.run() should catch KeyboardInterrupt, cancel the task,
        # and the task's finally block (calling service.stop()) should execute.
        logger.info(
            "Service interrupted by KeyboardInterrupt (caught at asyncio.run level)."
        )
    except Exception as e:
        # Catches exceptions re-raised from run_service_async_logic.
        logger.error(f"Service execution failed: {e}", exc_info=True)
        # The original code re-raised here. If desired, uncomment the next line.
        # raise

    logger.info("ManMan Subscribe Service stopped")
