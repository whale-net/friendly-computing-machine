import logging

from slack_bolt import Ack

from friendly_computing_machine.bot.app import SlackWebClientFCM, app
from friendly_computing_machine.bot.modal_schemas import ServerOption, ServerSelectModal
from friendly_computing_machine.bot.slack_payloads import ShortcutPayload

logger = logging.getLogger(__name__)

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
