import logging

from slack_bolt import Ack

from friendly_computing_machine.bot.app import SlackWebClientFCM, app
from friendly_computing_machine.bot.slack_payloads import ActionPayload
from friendly_computing_machine.manman.util import ManManAPI

logger = logging.getLogger(__name__)


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
        mapi.start_game_server_host_gameserver_id_start_post(1)  # testing for now

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
