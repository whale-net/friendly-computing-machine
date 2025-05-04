import logging

from slack_bolt import Ack

from friendly_computing_machine.bot.app import SlackWebClientFCM, app
from friendly_computing_machine.bot.modal_schemas import ServerActionModal
from friendly_computing_machine.bot.slack_payloads import ViewSubmissionPayload

logger = logging.getLogger(__name__)


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
