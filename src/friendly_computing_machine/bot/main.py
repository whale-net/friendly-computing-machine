import logging

from slack_bolt.adapter.socket_mode import SocketModeHandler

# Import handlers to register decorators with the app proxy
from friendly_computing_machine.bot import handlers  # noqa
from friendly_computing_machine.bot.app import get_slack_app  # Import app getter
from friendly_computing_machine.bot.task.taskpool import create_default_taskpool
from friendly_computing_machine.health import run_health_server
from friendly_computing_machine.util import NamedThreadPool

logger = logging.getLogger(__name__)


# NOTE: keep this here to avoid circular import
def run_slack_bot(app_token: str):  # ), bot_token: str):
    # for now, config is one time, requiring restart to reconfigure
    # also uses global, unsure hwo to pass additional context into slack event handler without it
    logger.info("starting slack bot")
    with NamedThreadPool() as executor:
        slack_socket_handler = SocketModeHandler(get_slack_app(), app_token)
        task_pool = create_default_taskpool()

        executor.submit(slack_socket_handler.start, thread_name="bolt")
        executor.submit(task_pool.start, thread_name="task")
        run_health_server()
        logger.info("slack bot work submit, should be running")
