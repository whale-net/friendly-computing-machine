import datetime
import threading
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dataclasses import dataclass
from friendly_computing_machine.models.slack import SlackMessageCreate
from friendly_computing_machine.db.db import (
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
    # testing
    t = threading.Thread(target=SocketModeHandler(app, app_token).start)
    t.start()
    print("socket thread started")
    t.join()


def slack_bot_who_am_i():
    print(app.client.auth_test())


def slack_send_message(channel: str, message: str):
    response = app.client.chat_postMessage(channel=channel, text=message)
    # our own messages aren't sent via event api
    # so need to insert them from the client response
    in_message = SlackMessageCreate(
        slack_id=None,
        slack_team_slack_id=response["message"].get("team"),
        slack_channel_slack_id=response.get("channel"),
        slack_user_slack_id=response["message"].get("user"),
        text=response["message"].get("text"),
        # unsure if message or response ts is more correct, or if it matters
        ts=ts_to_datetime(response["message"].get("ts")),
        thread_ts=response["message"].get("thread_ts"),
        parent_user_slack_id=response["message"].get("parent_user_id"),
    )

    out_message = insert_message(in_message)
    print(out_message)


@app.event("message")
def handle_message(event, say):
    # TODO: typehint for event? or am I supposed to just yolo it?
    # TODO: logging
    try:
        message = SlackMessageCreate(
            slack_id=event.get("client_msg_id"),
            slack_team_slack_id=event.get("team"),
            slack_channel_slack_id=event.get("channel"),  #
            slack_user_slack_id=event.get("user"),
            text=event.get("text"),
            ts=ts_to_datetime(event.get("ts")),
            thread_ts=event.get("thread_ts"),
            parent_user_slack_id=event.get("parent_user_id"),
        )
        print(event)

        # Rules for inserting messages
        # is in channel.is_music_poll
        # and
        # (
        #   is from bot user
        #   or
        #   is message in thread from bot user
        # )
        config = get_bot_config()

        # demorgans the above
        if message.slack_channel_slack_id not in config.MUSIC_POLL_CHANNEL_IDS:
            print(f"skipping message {message.slack_id} - not in music poll channel")
            return
        elif (
            message.slack_user_slack_id not in config.BOT_SLACK_USER_IDS
            and message.parent_user_slack_id not in config.BOT_SLACK_USER_IDS
        ):
            print(
                f"skipping message {message.slack_id} - not posted by bot user, or in bot user thread"
            )
            return

        # if we reach this point, we can insert the message
        # will be processed later
        msg = insert_message(message)
        print(f"message inserted: {msg}")
    except Exception as e:
        print(f"exception encountered: {e}")
        raise


def ts_to_datetime(ts: str):
    # yes ts is a str in the event payload
    return datetime.datetime.fromtimestamp(float(ts))
