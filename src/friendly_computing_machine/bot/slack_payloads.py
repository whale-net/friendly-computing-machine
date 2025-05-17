from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ShortcutPayload:
    trigger_id: str
    user_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShortcutPayload":
        return cls(
            trigger_id=data["trigger_id"],
            user_id=data["user"]["id"]
            if "user" in data and "id" in data["user"]
            else "",
        )


@dataclass
class ViewSubmissionPayload:
    trigger_id: str
    selected_server: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViewSubmissionPayload":
        try:
            selected_server = data["view"]["state"]["values"]["server_select_block"][
                "server_select_action"
            ]["selected_option"]["value"]
        except Exception:
            selected_server = None
        return cls(trigger_id=data["trigger_id"], selected_server=selected_server)


@dataclass
class ActionPayload:
    user_id: str
    custom_command: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActionPayload":
        try:
            custom_command = data["view"]["state"]["values"]["custom_input_block"][
                "custom_command_input"
            ]["value"]
        except Exception:
            custom_command = None
        return cls(user_id=data["user"]["id"], custom_command=custom_command)
