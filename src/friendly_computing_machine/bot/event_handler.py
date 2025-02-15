import datetime
import logging

from friendly_computing_machine.bot.app import app, get_bot_config
from friendly_computing_machine.db.dal import insert_message
from friendly_computing_machine.gemini.ai import generate_text_with_slack_context
from friendly_computing_machine.models.slack import SlackMessageCreate
from friendly_computing_machine.util import ts_to_datetime

from friendly_computing_machine.db.dal import (
    insert_genai_text,
    update_genai_text_response,
)
from friendly_computing_machine.models.genai import GenAITextCreate


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


# Name TBD, good enough for now, and doesn't reserve "ai" as a slash command
@app.command("/wai")
def handle_whale_ai_command(ack, say, command):
    ack()
    logger.info("slack-ack")

    user_name = command["user_name"]
    user_id = command["user_id"]
    channel_id = command["channel_id"]
    text = command["text"]

    # create and log request right away
    genai_text = insert_genai_text(
        GenAITextCreate(
            slack_channel_slack_id=channel_id,
            slack_user_slack_id=user_id,
            prompt=text,
            # TODO: am I stupid?
            created_at=datetime.datetime.now(),
        )
    )
    # ai_response, ai_feedback, ai_safety = generate_text(username, text)
    ai_response, _ = generate_text_with_slack_context(
        user_name, text, genai_text.slack_channel_slack_id
    )
    if ai_response is None:
        logger.info(
            "%s (%s) just triggered a bad response. See genai_text=%s",
            user_name,
            user_id,
            genai_text.id,
        )
        say(
            "error processing your response. It has been entirely ignored and you should feel bad for trying."
        )
        update_genai_text_response(
            genai_text_id=genai_text.id, response="WARNING: bad response produced"
        )

    update_genai_text_response(genai_text_id=genai_text.id, response=ai_response)

    say(text=ai_response)

    logger.info("successfully processed /wai")


@app.error
def global_error_handler(error, body, logger):
    """Handles errors globally."""
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")
