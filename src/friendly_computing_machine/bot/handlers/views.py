import logging

from slack_bolt import Ack

from friendly_computing_machine.bot.app import SlackWebClientFCM, app
from friendly_computing_machine.bot.modal_schemas import ServerActionModal
from friendly_computing_machine.bot.slack_payloads import ViewSubmissionPayload
from friendly_computing_machine.manman.api import OldManManAPI

logger = logging.getLogger(__name__)


@app.view("server_select_modal")
def handle_server_select_submission(ack: Ack, body, client: SlackWebClientFCM, logger):
    ack()
    try:
        payload = ViewSubmissionPayload.from_dict(body)

        if payload.selected_server is None:
            logger.error("No server selected")
            return

        server_config_id = int(payload.selected_server)
        logger.info(f"Server selected: {server_config_id}")
        manman = OldManManAPI.get_api()
        # TODO - add endpoint for just config info by id
        configs = manman.get_game_servers_host_gameserver_get()
        config = next(
            (
                config
                for config in configs
                if config.game_server_config_id == server_config_id
            ),
            None,
        )
        if config is None:
            logger.error(f"Server config not found for ID: {server_config_id}")
            return

        modal = ServerActionModal(
            server_name=config.name,
        )
        client.views_open(
            trigger_id=payload.trigger_id,
            # TODO - move arg out of build and into modal
            view=modal.build(
                game_server_instance_id=int(payload.selected_server)
                if payload.selected_server.isdigit()
                else -1
            ),
        )
        logger.info(f"Server manager opened for: {config.name}")
    except Exception as e:
        logger.error(f"Error opening server action modal: {e}")


@app.view("server_action_modal")
def handle_view_submission_events(ack, body, logger):
    ack()
    logger.info(body)


@app.view("poll_create_modal")
def handle_poll_create_submission(ack: Ack, body, client: SlackWebClientFCM, logger):
    """Handle poll creation modal submission."""
    ack()

    try:
        import datetime

        from friendly_computing_machine.bot.util import slack_send_message
        from friendly_computing_machine.db.dal.poll_dal import (
            insert_poll,
            insert_poll_options,
            update_poll_message_info,
        )
        from friendly_computing_machine.models.poll import PollCreate, PollOptionCreate
        from friendly_computing_machine.temporal.poll_workflow import (
            PollWorkflow,
            PollWorkflowParams,
        )
        from friendly_computing_machine.temporal.util import (
            execute_workflow,
            get_temporal_queue_name,
        )

        # Extract form data
        values = body["view"]["state"]["values"]

        # Required fields
        title = values["poll_title_block"]["poll_title_input"]["value"]
        option1 = values["poll_option_1_block"]["poll_option_1_input"]["value"]
        option2 = values["poll_option_2_block"]["poll_option_2_input"]["value"]

        # Optional fields
        description = (
            values.get("poll_description_block", {})
            .get("poll_description_input", {})
            .get("value")
        )
        option3 = (
            values.get("poll_option_3_block", {})
            .get("poll_option_3_input", {})
            .get("value")
        )
        option4 = (
            values.get("poll_option_4_block", {})
            .get("poll_option_4_input", {})
            .get("value")
        )
        option5 = (
            values.get("poll_option_5_block", {})
            .get("poll_option_5_input", {})
            .get("value")
        )

        # Get user and channel info
        user_id = body["user"]["id"]
        channel_id = body["view"]["private_metadata"]

        if not channel_id:
            logger.error("No channel ID found in private_metadata")
            return

        # Create poll in database
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=8)
        poll_create = PollCreate(
            title=title,
            description=description,
            slack_channel_slack_id=channel_id,
            slack_user_slack_id=user_id,
            created_at=datetime.datetime.now(),
            expires_at=expires_at,
            is_active=True,
        )

        poll = insert_poll(poll_create)
        logger.info(f"Created poll with ID: {poll.id}")

        # Create poll options
        options_data = [(option1, 1), (option2, 2)]
        if option3:
            options_data.append((option3, 3))
        if option4:
            options_data.append((option4, 4))
        if option5:
            options_data.append((option5, 5))

        poll_options = [
            PollOptionCreate(poll_id=poll.id, text=text, display_order=order)
            for text, order in options_data
        ]

        insert_poll_options(poll_options)
        logger.info(f"Created {len(poll_options)} options for poll {poll.id}")

        # Send initial poll message to channel
        initial_message = f"📊 **{title}**"
        if description:
            initial_message += f"\n_{description}_"
        initial_message += "\n\n_Setting up poll..._"

        slack_message = slack_send_message(
            channel=channel_id,
            message=initial_message,
        )

        # Update poll with message info
        update_poll_message_info(
            poll.id, slack_message.id, slack_message.ts.isoformat()
        )

        # Start temporal workflow
        workflow_id = f"poll-workflow-{poll.id}-{datetime.datetime.now().isoformat()}"

        # Update poll with workflow ID
        from friendly_computing_machine.db.dal.poll_dal import update_poll_workflow_id

        update_poll_workflow_id(poll.id, workflow_id)

        execute_workflow(
            PollWorkflow.run,
            PollWorkflowParams(poll_id=poll.id, duration_hours=8),
            id=workflow_id,
            task_queue=get_temporal_queue_name("main"),
        )

        logger.info(f"Started poll workflow {workflow_id} for poll {poll.id}")

    except Exception as e:
        logger.exception(f"Error creating poll: {e}")
        # In a real app, you might want to show an error message to the user
