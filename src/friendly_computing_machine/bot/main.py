import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dataclasses import dataclass
from friendly_computing_machine.util import NamedThreadPool
from friendly_computing_machine.db.dal import (
    get_music_poll_channel_slack_ids,
    get_bot_slack_user_slack_ids,
)
from friendly_computing_machine.bot.task import create_default_taskpool


# it is stupid as hell but I guess I need to create this out here with a token from env
# It does not seem possible to create it here, use for decorators, and then authenticate during runtime
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

__GLOBALS = {
    "bot_config": None,
}


@dataclass
class SlackBotConfig:
    MUSIC_POLL_CHANNEL_IDS: set[str]
    BOT_SLACK_USER_IDS: set[str]


def init_bot_config():
    if __GLOBALS["bot_config"] is not None:
        raise RuntimeError("double bot_config init")
    __GLOBALS["bot_config"] = SlackBotConfig(
        MUSIC_POLL_CHANNEL_IDS=get_music_poll_channel_slack_ids(),
        BOT_SLACK_USER_IDS=get_bot_slack_user_slack_ids(),
    )


def get_bot_config() -> SlackBotConfig:
    if __GLOBALS["bot_config"] is None:
        raise RuntimeError("bot_config is none")
    return __GLOBALS["bot_config"]


# Start your app
def run_slack_bot(app_token: str):  # ), bot_token: str):
    # for now, config is one time, requiring restart to reconfigure
    # also uses global, unsure hwo to pass additional context into slack event handler without it
    init_bot_config()
    print("got config")

    with NamedThreadPool() as executor:
        slack_socket_handler = SocketModeHandler(app, app_token)
        executor.submit(slack_socket_handler.start, thread_name="bolt")

        task_pool = create_default_taskpool()
        executor.submit(task_pool.start, thread_name="task")
