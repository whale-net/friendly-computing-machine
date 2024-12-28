import logging

from friendly_computing_machine.bot.app import app, get_bot_config
from friendly_computing_machine.db.dal import insert_message
from friendly_computing_machine.models.slack import SlackMessageCreate
from friendly_computing_machine.util import ts_to_datetime

logger = logging.getLogger(__name__)


@app.event("message")
def handle_message(event, say):
    # TODO: typehint for event? or am I supposed to just yolo it?
    # TODO: logging
    try:
        logger.debug(event)
        sub_type = event.get("subtype", "")
        if sub_type == "message_changed":
            # TODO - update message - for now, will use latest message for poll
            logger.info("message update received. not updating, not implemented (yet)")
            return
        else:
            message_event = event

        thread_ts = message_event.get("thread_ts")
        message = SlackMessageCreate(
            slack_id=message_event.get("client_msg_id"),
            slack_team_slack_id=message_event.get("team"),
            slack_channel_slack_id=message_event.get("channel"),  #
            slack_user_slack_id=message_event.get("user"),
            text=message_event.get("text"),
            ts=ts_to_datetime(event.get("ts")),
            thread_ts=ts_to_datetime(thread_ts) if thread_ts else None,
            parent_user_slack_id=event.get("parent_user_id"),
        )

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
            logger.info(
                "skipping message %s - not in music poll channel", message.slack_id
            )
            return
        elif (
            message.slack_user_slack_id not in config.BOT_SLACK_USER_IDS
            and message.parent_user_slack_id not in config.BOT_SLACK_USER_IDS
        ):
            logger.info(
                "skipping message %s - not posted by bot user, or in bot user thread",
                message.slack_id,
            )
            return

        # if we reach this point, we can insert the message
        # will be processed later
        msg = insert_message(message)
        logger.info("message inserted. id=%s, slack_id=%s", msg.id, msg.slack_id)
    except Exception as e:
        logger.warning("exception encountered: %s", e)
        raise
