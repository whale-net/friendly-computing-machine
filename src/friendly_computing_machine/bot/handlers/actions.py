import logging
import re

from slack_bolt import Ack

from external.manman_experience_api.models import StdinCommandRequest
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
    payload = ActionPayload.from_dict(body)
    # TODO - improve this
    raw_string = payload.action_body
    id, command = raw_string.split(";", 1)
    # TODO - pass in command_args as list instead of a single string
    mmexapi = ManManExperienceAPI.get_api()
    # TODO  does work?
    if not command:
        logger.error("No command provided in stdin action")
        ack(text="No command provided")
        return
    mmexapi.stdin_game_server_gameserver_id_stdin_post(
        int(id),
        StdinCommandRequest(commands=[command]),
    )
    ack()


@app.action(SlackActionRegistry.MANMAN_WORKER_STOP)
def handle_manman_worker_stop(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    logger.info("ManMan worker stop action triggered")
    mmexapi = ManManExperienceAPI.get_api()
    # This is kind of risky because it shuts down the current worker
    # but it is the only way to stop a worker in ManMan Experience atm
    # eventually we should have a proper stop endpoint with ID to avoid this weirdness
    mmexapi.worker_shutdown_worker_shutdown_post()
    ack()


@app.action(SlackActionRegistry.MANMAN_SERVER_CREATE)
def handle_manman_server_create(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    logger.info("ManMan server create action triggered")
    payload = ActionPayload.from_dict(body)
    # not ideal, but we need to get the server ID from the private metadata
    # eventually this should be custom dataclasses and the such
    server_id = int(payload.action_body)
    mmexapi = ManManExperienceAPI.get_api()
    mmexapi.start_game_server_gameserver_id_start_post(server_id)
    ack()


@app.action(re.compile(f"^{SlackActionRegistry.MANMAN_SERVER_STDIN}_"))
def handle_manman_server_stdin(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    logger.info("ManMan server stdin action triggered")

    payload = ActionPayload.from_dict(body)
    # TODO - improve this
    raw_string = payload.action_body
    id, command = raw_string.split(";", 1)
    # TODO - pass in command_args as list instead of a single string
    mmexapi = ManManExperienceAPI.get_api()
    # TODO  does work?
    mmexapi.stdin_game_server_gameserver_id_stdin_post(
        int(id),
        StdinCommandRequest(commands=[command]),
    )
    ack()


@app.action(SlackActionRegistry.MANMAN_SERVER_STOP)
def handle_manman_server_stop(
    ack: Ack, body, client: SlackWebClientFCM, logger: logging.Logger
):
    payload = ActionPayload.from_dict(body)
    logger.info("ManMan server stop action triggered")
    # not ideal, but we need to get the server ID from the private metadata
    # eventually this should be custom dataclasses and the such
    server_id = int(payload.action_body)
    mmexapi = ManManExperienceAPI.get_api()
    mmexapi.stop_game_server_gameserver_id_stop_post(server_id)
    ack(":( bye bye")

    # TODO 6/10/25
    # something is wrong with the stop. It is being passed the right id I think
    # but it's not doing anything on the server.
    # need more debug information in the server in this csae
    # also need to fix rabbitmq timeout issue or whatever that keeps happening in local terminal
    # also need proper worker and server instance ids chained to actios
    # and base classes for passing that metadata around


@app.action(re.compile(r"^poll_vote_\d+_\d+$"))
def handle_poll_vote(ack: Ack, body, client: SlackWebClientFCM, logger):
    """Handle poll vote button clicks."""
    ack()
    
    try:
        from friendly_computing_machine.db.dal.poll_dal import insert_poll_vote, get_poll_by_id
        from friendly_computing_machine.models.poll import PollVoteCreate
        from friendly_computing_machine.temporal.poll_workflow import PollUpdateActivityParams, update_poll_message_activity
        from friendly_computing_machine.temporal.util import execute_activity
        import datetime
        
        # Parse action_id to get poll_id and option_id
        action_id = body["actions"][0]["action_id"]
        # Format: poll_vote_{poll_id}_{option_id}
        parts = action_id.split("_")
        poll_id = int(parts[2])
        option_id = int(parts[3])
        
        user_id = body["user"]["id"]
        
        logger.info(f"User {user_id} voting for option {option_id} in poll {poll_id}")
        
        # Check if poll is still active
        poll = get_poll_by_id(poll_id)
        if not poll or not poll.is_active:
            ack("This poll is no longer active.")
            return
        
        # Record the vote
        vote_create = PollVoteCreate(
            poll_id=poll_id,
            poll_option_id=option_id,
            slack_user_slack_id=user_id,
            created_at=datetime.datetime.now(),
        )
        
        insert_poll_vote(vote_create)
        logger.info(f"Recorded vote for user {user_id} in poll {poll_id}")
        
        # Trigger immediate poll message update
        # Note: We'll call this synchronously since we're not in an async context
        # In production, you might want to queue this update or use a different mechanism
        try:
            # Import the function directly and call it synchronously
            from friendly_computing_machine.temporal.poll_workflow import _update_poll_message
            _update_poll_message(poll_id)
        except Exception as e:
            logger.warning(f"Failed to trigger immediate poll update: {e}")
        
        # Send ephemeral confirmation to the user
        client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=user_id,
            text="✅ Your vote has been recorded!"
        )
        
    except Exception as e:
        logger.exception(f"Error handling poll vote: {e}")
        client.chat_postEphemeral(
            channel=body["channel"]["id"],
            user=body["user"]["id"],
            text="❌ Sorry, there was an error recording your vote. Please try again."
        )
