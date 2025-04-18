import logging

from slack_bolt.adapter.socket_mode import SocketModeHandler

from friendly_computing_machine.bot.app import app
from friendly_computing_machine.bot.task.taskpool import create_default_taskpool
from friendly_computing_machine.util import NamedThreadPool
from friendly_computing_machine.health import run_health_server

logger = logging.getLogger(__name__)


# NOTE: keep this here to avoid circular import
def run_slack_bot(
    app_token: str, temporal_host: str, app_env: str
):  # ), bot_token: str):
    # for now, config is one time, requiring restart to reconfigure
    # also uses global, unsure hwo to pass additional context into slack event handler without it
    logger.info("starting slack bot")
    with NamedThreadPool() as executor:
        slack_socket_handler = SocketModeHandler(app, app_token)
        task_pool = create_default_taskpool()

        executor.submit(slack_socket_handler.start, thread_name="bolt")
        executor.submit(task_pool.start, thread_name="task")
        run_health_server()
        logger.info("slack bot work submit, should be running")
