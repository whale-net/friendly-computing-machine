import datetime
import logging

from opentelemetry import trace
from slack_bolt import Ack

from friendly_computing_machine.bot.app import SlackWebClientFCM, app, get_bot_config
from friendly_computing_machine.bot.modal_schemas import (
    ServerActionModal,
    ServerOption,
    ServerSelectModal,
)
from friendly_computing_machine.bot.slack_payloads import (
    ActionPayload,
    ShortcutPayload,
    ViewSubmissionPayload,
)
from friendly_computing_machine.db.dal import (
    insert_genai_text,
    insert_slack_command,
    update_genai_text_response,
    upsert_message,
)
from friendly_computing_machine.manman.util import ManManAPI
from friendly_computing_machine.models.genai import GenAITextCreate
from friendly_computing_machine.models.slack import (
    SlackCommandCreate,
    SlackMessageCreate,
)
from friendly_computing_machine.temporal.slack.workflow import (
    SlackContextGeminiWorkflow,
    SlackContextGeminiWorkflowParams,
)
from friendly_computing_machine.temporal.util import (
    execute_workflow,
    get_temporal_queue_name,
)

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@app.event("message")
def handle_message(event, say):
    # TODO: typehint for event? or am I supposed to just yolo it?
    with tracer.start_as_current_span("handle_message") as span:
        try:
            logger.debug(event)
            sub_type = event.get("subtype", "")
            span.set_attribute("slack.event.subtype", sub_type)

            if sub_type == "message_changed":
                # TODO - update message - for now, will use latest message for poll
                logger.info(
                    "message update received. not updating, not implemented (yet)"
                )
                span.set_attribute("message.processed", False)
                span.set_attribute("message.reason", "message_changed subtype")
                return
            else:
                message_event = event

            message = SlackMessageCreate.from_slack_message_json(message_event)
            span.set_attribute("slack.message.id", message.slack_id)
            span.set_attribute("slack.channel.id", message.slack_channel_slack_id)
            span.set_attribute("slack.user.id", message.slack_user_slack_id)

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
                span.set_attribute("message.processed", False)
                span.set_attribute("message.reason", "not in music poll channel")
                return

            # if we reach this point, we can insert the message
            # will be processed later
            msg = upsert_message(message)
            span.set_attribute("db.message.id", msg.id)
            span.set_attribute("message.processed", True)
            logger.info("message inserted. id=%s, slack_id=%s", msg.id, msg.slack_id)
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


# Name TBD, good enough for now, and doesn't reserve "ai" as a slash command
@app.command("/wai")
def handle_whale_ai_command(ack, say, command):
    with tracer.start_as_current_span("handle_whale_ai_command") as span:
        try:
            ack()
            logger.info("slack-ack")

            user_name = command["user_name"]
            user_id = command["user_id"]
            channel_id = command["channel_id"]
            text = command["text"]

            span.set_attribute("slack.command", "/wai")
            span.set_attribute("slack.user.id", user_id)
            span.set_attribute("slack.user.name", user_name)
            span.set_attribute("slack.channel.id", channel_id)
            span.set_attribute("slack.command.text", text)

            # TODO - move this entirely to the workflow
            # it is dangerous to do this here, because we are not in a transaction
            # and we don't want to pollute the database with a command that is not processed.
            # Addiionally, temporal will not be able to retry this if it fails.
            # use child workflow if we don't want to pollute existing workflow (probably a good idea, although not needed now)
            # be aggressive on concurrency
            command_create = SlackCommandCreate(
                caller_slack_user_id=user_id,
                command_base="/wai",
                command_text=text,
                slack_channel_slack_id=channel_id,
                created_at=datetime.datetime.now(),
            )
            db_command = insert_slack_command(command_create)
            span.set_attribute("db.command.inserted", True)
            span.set_attribute("db.command.id", db_command.id)

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
            span.set_attribute("db.genai_text.id", genai_text.id)
            # remove old method and replace with temporal
            # ai_response, ai_feedback, ai_safety = generate_text(username, text)
            # ai_response, _ = generate_text_with_slack_context(
            #     user_name, text, genai_text.slack_channel_slack_id
            # )
            workflow_id = f"test_id-command-wai-{channel_id}-{datetime.datetime.now()}"
            span.set_attribute("temporal.workflow.id", workflow_id)
            ai_response = execute_workflow(
                SlackContextGeminiWorkflow.run,
                SlackContextGeminiWorkflowParams(channel_id, text),
                id=workflow_id,
                # TODO - proper task queue differentation at some point
                task_queue=get_temporal_queue_name("main"),
            )
            span.set_attribute("temporal.workflow.executed", True)

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
                    genai_text_id=genai_text.id,
                    response="WARNING: bad response produced",
                )
                span.set_attribute("ai.response.status", "bad_response")
            else:
                update_genai_text_response(
                    genai_text_id=genai_text.id, response=ai_response
                )
                span.set_attribute("db.genai_text.response_updated", True)
                say(text=ai_response)
                span.set_attribute("slack.response.sent", True)
                span.set_attribute("ai.response.status", "success")

            logger.info("successfully processed /wai")
            span.set_status(trace.Status(trace.StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.exception("Error handling /wai command")
            # Reraise exception to be caught by global handler
            raise


@app.error
def global_error_handler(error, body, logger):
    """Handles errors globally."""
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")


# --- Server Control Modal Handlers ---

DUMMY_SERVERS = [
    ServerOption(label="Server Alpha", value="server_alpha"),
    ServerOption(label="Server Beta", value="server_beta"),
    ServerOption(label="Server Gamma", value="server_gamma"),
]


@app.shortcut("server_control_shortcut")
def open_server_select_modal(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    try:
        payload = ShortcutPayload.from_dict(body)
        modal = ServerSelectModal(options=DUMMY_SERVERS)
        client.views_open(
            trigger_id=payload.trigger_id,
            view=modal.build(),
        )
    except Exception as e:
        logger.error(f"Error opening server select modal: {e}")


@app.view("server_select_modal")
def handle_server_select_submission(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    try:
        payload = ViewSubmissionPayload.from_dict(body)
        modal = ServerActionModal(
            server_name=(payload.selected_server or "Unknown").replace("_", " ").title()
        )
        client.views_open(
            trigger_id=payload.trigger_id,
            view=modal.build(),
        )
    except Exception as e:
        logger.error(f"Error opening server action modal: {e}")


@app.action("start_server")
def handle_start_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Start server clicked")
    client.chat_postMessage(
        channel=payload.user_id, text="[Stub] Start server action triggered."
    )
    # Use the ManManAPI class to get the client
    try:
        # perhaps a rather unfortunate name
        mapi = ManManAPI.get_api()
        mapi.start_game_server_host_gameserver_id_start_post(
            1  # testing for now
        )

    except ValueError as e:
        logger.error(f"Failed to get ManMan API client: {e}")
        # Optionally inform the user about the configuration issue
        client.chat_postMessage(
            channel=payload.user_id, text="Error: ManMan API is not configured."
        )


@app.action("stop_server")
def handle_stop_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Stop server clicked")
    client.chat_postMessage(
        channel=payload.user_id, text="[Stub] Stop server action triggered."
    )


@app.action("restart_server")
def handle_restart_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Restart server clicked")
    client.chat_postMessage(
        channel=payload.user_id, text="[Stub] Restart server action triggered."
    )


@app.action("send_custom_command")
def handle_custom_command(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info(f"Custom command sent: {payload.custom_command}")
    client.chat_postMessage(
        channel=payload.user_id,
        text=f"[Stub] Custom command sent: {payload.custom_command}",
    )
