from slack_sdk.models.blocks import Option

from external.manman_api.models.game_server_config import GameServerConfig
from external.manman_api.models.game_server_instance_output import (
    GameServerInstanceOutput,
)
from friendly_computing_machine.bot.modal_schemas import ServerSelectModal
from friendly_computing_machine.manman.api import ManManAPI


def build_server_select_modal() -> ServerSelectModal:
    manman = ManManAPI.get_api()
    active_server_response = (
        manman.get_active_game_server_instances_host_gameserver_instances_active_get()
    )
    servers: list[GameServerInstanceOutput] = (
        active_server_response.game_server_instances
    )
    configs: list[GameServerConfig] = active_server_response.configs
    config_map = {config.game_server_config_id: config for config in configs}

    options = [
        Option(
            label=config_map[server.game_server_config_id].name,
            value=str(server.game_server_instance_id),
        )
        for server in servers
    ]
    modal = ServerSelectModal(options=options)
    return modal
