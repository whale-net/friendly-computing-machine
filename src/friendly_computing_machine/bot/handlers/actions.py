import logging

from external.manman_api.models.stdin_command_request import StdinCommandRequest
from slack_bolt import Ack

from friendly_computing_machine.bot.app import app
from friendly_computing_machine.bot.slack_client import SlackWebClientFCM
from friendly_computing_machine.bot.slack_payloads import ActionPayload
from friendly_computing_machine.manman.api import ManManAPI

logger = logging.getLogger(__name__)


@app.action("start_server")
def handle_start_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Start server clicked")
    # Use the ManManAPI class to get the client
    try:
        mapi = ManManAPI.get_api()
        game_server_config_id = int(payload.private_metadata)
        mapi.start_game_server_host_gameserver_id_start_post(game_server_config_id)
        logger.info("started %s", game_server_config_id)
    except ValueError as e:
        logger.error(f"Failed to get ManMan API client: {e}")
        # Optionally inform the user about the configuration issue
        client.chat_postMessage(
            channel=payload.user_id, text="Error: ManMan API is not configured."
        )


@app.action("stop_server")
def handle_stop_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    logger.debug(body)
    payload = ActionPayload.from_dict(body)
    logger.info("Stop server clicked")
    try:
        mapi = ManManAPI.get_api()
        game_server_config_id = int(payload.private_metadata)
        mapi.stop_game_server_host_gameserver_id_stop_post(game_server_config_id)
    except Exception as e:
        logger.exception(f"Failed to get ManMan API client: {e}")
        # Optionally inform the user about the configuration issue
        client.chat_postMessage(
            channel=payload.user_id, text="Error: ManMan API is not configured."
        )


@app.action("restart_server")
def handle_restart_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Restart server clicked")
    client.chat_postMessage(
        channel=payload.user_id,
        text="[Stub] Restart server action triggered. Currently does nothing.",
    )


@app.action("send_stdin_custom_command")
def handle_custom_command(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.debug(body)

    if payload.custom_command is None:
        logger.error("Custom command is None")
        # message?
        client.chat_postMessage(
            channel=payload.user_id, text="Error: Custom command is empty."
        )
        return

    logger.info(f"Custom command: {payload.custom_command}")

    # TODO - parse this? seems rather wrong to just take user input but whatever for now
    req = StdinCommandRequest(
        commands=[payload.custom_command],
    )
    try:
        mapi = ManManAPI.get_api()
        game_server_instance_id = int(payload.private_metadata)
        mapi.stdin_game_server_host_gameserver_id_stdin_post(
            game_server_instance_id,
            req,
        )
    except Exception as e:
        logger.exception(f"Failed to get ManMan API client: {e}")
        # Optionally inform the user about the configuration issue
        client.chat_postMessage(
            channel=payload.user_id, text="Error: ManMan API error. Please try again"
        )
