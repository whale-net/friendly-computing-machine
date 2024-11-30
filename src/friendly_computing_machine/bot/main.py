from datetime import datetime, timedelta


from slack_bolt.adapter.socket_mode import SocketModeHandler
from dataclasses import dataclass
from friendly_computing_machine.util import NamedThreadPool
from friendly_computing_machine.db.dal import (
    get_music_poll_channel_slack_ids,
    get_bot_slack_user_slack_ids,
)
from friendly_computing_machine.bot.task.taskpool import create_default_taskpool
from friendly_computing_machine.bot.app import app


# it is stupid as hell but I guess I need to create this out here with a token from env
# It does not seem possible to create it here, use for decorators, and then authenticate during runtime


__GLOBALS = {}


@dataclass
class SlackBotConfig:
    MUSIC_POLL_CHANNEL_IDS: set[str]
    BOT_SLACK_USER_IDS: set[str]
    as_of: datetime

    REFRESH_PERIOD: timedelta = timedelta(minutes=1)

    @classmethod
    def create(cls):
        return SlackBotConfig(
            MUSIC_POLL_CHANNEL_IDS=get_music_poll_channel_slack_ids(),
            BOT_SLACK_USER_IDS=get_bot_slack_user_slack_ids(),
            as_of=datetime.now(),
        )


def get_bot_config() -> SlackBotConfig:
    config = __GLOBALS.get("bot_config")
    if config is None:
        config = SlackBotConfig.create()
    elif config.as_of + SlackBotConfig.REFRESH_PERIOD < datetime.now():
        config = SlackBotConfig.create()

    return config


# Start your app
def run_slack_bot(app_token: str):  # ), bot_token: str):
    # for now, config is one time, requiring restart to reconfigure
    # also uses global, unsure hwo to pass additional context into slack event handler without it

    with NamedThreadPool() as executor:
        slack_socket_handler = SocketModeHandler(app, app_token)
        task_pool = create_default_taskpool()

        executor.submit(slack_socket_handler.start, thread_name="bolt")
        executor.submit(task_pool.start, thread_name="task")
