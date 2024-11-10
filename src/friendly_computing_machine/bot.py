import datetime
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dataclasses import dataclass
from friendly_computing_machine.models import SlackMessageCreate
from friendly_computing_machine.db import (
    get_music_poll_channel_slack_ids,
    get_bot_slack_user_slack_ids,
    insert_message,
)

# Initializes your app with your bot token and socket mode handler

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
    return SlackBotConfig(
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
    SocketModeHandler(app, app_token).start()


@app.event("message")
def handle_message(event, say):
    # config = get_bot_config()

    # TODO: typehint for event? or am I supposed to just yolo it?
    print(event)

    message = SlackMessageCreate(
        slack_id=event.get("client_msg_id"),
        slack_team_slack_id=event.get("team"),
        slack_channel_slack_id=event.get("channel"),
        slack_user_slack_id=event.get("user"),
        text=event.get("text"),
        ts=ts_to_datetime(event.get("ts")),
        thread_ts=event.get("thread_ts"),
        parent_user_slack_id=event.get("parent_user_id"),
    )

    if event.get("thread_ts") is not None:
        insert_message(message)


def ts_to_datetime(ts: str):
    # yes ts is a str in the event payload
    return datetime.datetime.fromtimestamp(float(ts))
