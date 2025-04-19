import datetime
import logging

from friendly_computing_machine.bot.app import app, get_bot_config
from friendly_computing_machine.bot.workflow import (
    SlackConextGeminiWorkflow,
    SlackContextGeminiWorkflowParams,
)
from friendly_computing_machine.db.dal import (
    insert_genai_text,
    insert_slack_command,
    update_genai_text_response,
    upsert_message,
)
from friendly_computing_machine.models.genai import GenAITextCreate
from friendly_computing_machine.models.slack import (
    SlackCommandCreate,
    SlackMessageCreate,
)
from friendly_computing_machine.temporal.util import (
    execute_workflow,
    get_temporal_queue_name,
)

logger = logging.getLogger(__name__)


@app.event("message")
def handle_message(event, say):
    # TODO: typehint for event? or am I supposed to just yolo it?
    try:
        logger.debug(event)
        sub_type = event.get("subtype", "")
        if sub_type == "message_changed":
            # TODO - update message - for now, will use latest message for poll
            logger.info("message update received. not updating, not implemented (yet)")
            return
        else:
            message_event = event

        message = SlackMessageCreate.from_slack_message_json(message_event)

        # Rules for inserting messages
        # is in channel.is_music_poll
        # there used to be a rule about bot user, bot thread, but that was removed
        config = get_bot_config()

        if message.slack_channel_slack_id not in {
            info.slack_channel.slack_id for info in config.music_poll_infos
        }:
            logger.info(
                "skipping message %s - not in music poll channel", message.slack_id
            )
            return

        # if we reach this point, we can insert the message
        # will be processed later
        msg = upsert_message(message)
        logger.info("message inserted. id=%s, slack_id=%s", msg.id, msg.slack_id)
    except Exception:
        raise


# Name TBD, good enough for now, and doesn't reserve "ai" as a slash command
@app.command("/wai")
def handle_whale_ai_command(ack, say, command):
    try:
        ack()
        logger.info("slack-ack")

        user_name = command["user_name"]
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = command["text"]

        command_create = SlackCommandCreate(
            caller_slack_user_id=user_id,
            command_base="/wai",
            command_text=text,
            slack_channel_slack_id=channel_id,
            created_at=datetime.datetime.now(),
        )
        insert_slack_command(command_create)

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
        # remove old method and replace with temporal
        # ai_response, ai_feedback, ai_safety = generate_text(username, text)
        # ai_response, _ = generate_text_with_slack_context(
        #     user_name, text, genai_text.slack_channel_slack_id
        # )
        ai_response = execute_workflow(
            SlackConextGeminiWorkflow.run,
            SlackContextGeminiWorkflowParams(channel_id, text),
            id=f"test_id-command-wai-{channel_id}-{datetime.datetime.now()}",
            # TODO - proper task queue differentation at some point
            task_queue=get_temporal_queue_name("main"),
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
    except Exception:
        raise


@app.error
def global_error_handler(error, body, logger):
    """Handles errors globally."""
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")
