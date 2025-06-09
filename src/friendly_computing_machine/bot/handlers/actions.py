import logging

from slack_bolt import Ack

from external.old_manman_api.models.stdin_command_request import StdinCommandRequest
from friendly_computing_machine.bot.app import app
from friendly_computing_machine.bot.slack_client import SlackWebClientFCM
from friendly_computing_machine.bot.slack_enum import SlackActionRegistry
from friendly_computing_machine.bot.slack_payloads import ActionPayload
from friendly_computing_machine.manman.api import ManManExperienceAPI, OldManManAPI

logger = logging.getLogger(__name__)


@app.action("start_server")
def handle_start_server(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("Start server clicked")
    # Use the ManManAPI class to get the client
    try:
        mapi = OldManManAPI.get_api()
        game_server_config_id = int(payload.action_body)
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
        mapi = OldManManAPI.get_api()
        game_server_config_id = int(payload.action_body)
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

    if payload.stdin_command_input is None:
        logger.error("Custom command is None")
        # message?
        client.chat_postMessage(
            channel=payload.user_id, text="Error: Custom command is empty."
        )
        return

    logger.info(f"Custom command: {payload.stdin_command_input}")

    # TODO - parse this? seems rather wrong to just take user input but whatever for now
    req = StdinCommandRequest(
        commands=[payload.stdin_command_input],
    )
    try:
        mapi = OldManManAPI.get_api()
        game_server_instance_id = int(payload.action_body)
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


@app.action(SlackActionRegistry.MANMAN_WORKER_STOP)
def handle_manman_worker_stop(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    ack()
    logger.info("ManMan worker stop action triggered")
    mmexapi = ManManExperienceAPI.get_api()
    # This is kind of risky because it shuts down the current worker
    # but it is the only way to stop a worker in ManMan Experience atm
    # eventually we should have a proper stop endpoint with ID to avoid this weirdness
    mmexapi.worker_shutdown_worker_shutdown_post()


@app.action(SlackActionRegistry.MANMAN_SERVER_CREATE)
def handle_manman_server_create(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    ack()
    logger.info("ManMan server create action triggered")
    payload = ActionPayload.from_dict(body)
    # not ideal, but we need to get the server ID from the private metadata
    # eventually this should be custom dataclasses and the such
    server_id = int(payload.action_body)
    mmexapi = ManManExperienceAPI.get_api()
    mmexapi.start_game_server_gameserver_id_start_post(server_id)


@app.action(SlackActionRegistry.MANMAN_SERVER_STDIN)
def handle_manman_server_stdin(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    ack()
    logger.info("ManMan server stdin action triggered")

    # payload = ActionPayload.from_dict(body)
    # mmexapi = ManManExperienceAPI.get_api()

    logger.info(
        "Not implemented yet, but this is where we would handle stdin for a ManMan server."
    )


@app.action(SlackActionRegistry.MANMAN_SERVER_STOP)
def handle_manman_server_stop(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    ack()
    payload = ActionPayload.from_dict(body)
    logger.info("ManMan server stop action triggered")
    # not ideal, but we need to get the server ID from the private metadata
    # eventually this should be custom dataclasses and the such
    server_id = int(payload.action_body)
    mmexapi = ManManExperienceAPI.get_api()
    mmexapi.stop_game_server_gameserver_id_stop_post(server_id)
