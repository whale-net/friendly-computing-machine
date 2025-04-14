import logging
from datetime import datetime
from typing import Optional

from friendly_computing_machine.bot.app import app
from friendly_computing_machine.db.dal import insert_message
from friendly_computing_machine.models.slack import SlackMessage, SlackMessageCreate
from friendly_computing_machine.util import ts_to_datetime

logger = logging.getLogger(__name__)


def slack_send_message(
    channel: str, message: str, thread_ts: Optional[datetime] = None
) -> SlackMessage:
    logger.info("sending message %s", message)
    thread_ts_str = None
    if thread_ts is not None:
        thread_ts_str = str(thread_ts.timestamp())
    response = app.client.chat_postMessage(
        channel=channel, text=message, thread_ts=thread_ts_str
    )
    logger.info(
        "message sent, is response ok? %s", "yes" if response.get("ok") else "no"
    )
    # our own messages aren't sent via event api
    # so need to insert them from the client response
    response_thread_ts = response["message"].get("thread_ts")
    in_message = SlackMessageCreate(
        slack_id=None,
        slack_team_slack_id=response["message"].get("team"),
        slack_channel_slack_id=response.get("channel"),
        slack_user_slack_id=response["message"].get("user"),
        text=response["message"].get("text"),
        # unsure if message or response ts is more correct, or if it matters
        # TODO - check if this is giving wrong timezone
        ts=ts_to_datetime(response["message"].get("ts")),
        thread_ts=ts_to_datetime(response_thread_ts) if response_thread_ts else None,
        parent_user_slack_id=response["message"].get("parent_user_id"),
    )
    logger.debug("in_message: %s", in_message)

    out_message = insert_message(in_message)
    return out_message


def slack_bot_who_am_i():
    return app.client.auth_test()
