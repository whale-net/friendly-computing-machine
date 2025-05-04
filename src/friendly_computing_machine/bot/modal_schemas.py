from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ServerOption:
    label: str
    value: str

    def to_slack_option(self) -> Dict[str, Any]:
        return {
            "text": {"type": "plain_text", "text": self.label},
            "value": self.value,
        }


@dataclass
class ServerSelectModal:
    options: List[ServerOption]
    callback_id: str = "server_select_modal"
    title: str = "Select Server"
    submit_text: str = "Next"

    def build(self) -> Dict[str, Any]:
        return {
            "type": "modal",
            "callback_id": self.callback_id,
            "title": {"type": "plain_text", "text": self.title},
            "submit": {"type": "plain_text", "text": self.submit_text},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "server_select_block",
                    "label": {"type": "plain_text", "text": "Choose a server"},
                    "element": {
                        "type": "static_select",
                        "action_id": "server_select_action",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a server",
                        },
                        "options": [opt.to_slack_option() for opt in self.options],
                    },
                }
            ],
        }


@dataclass
class ServerActionModal:
    server_name: str
    callback_id: str = "server_action_modal"
    title: str = "Server Actions"
    # submit_text: str = "Submit"  # Added submit text
    actions: List[str] = field(default_factory=lambda: ["Start", "Stop", "Restart"])
    custom_button_text: str = "Send Custom"

    def build(self) -> Dict[str, Any]:
        return {
            "type": "modal",
            # "submit": {"type": "plain_text", "text": self.submit_text}, # Added submit button definition
            "callback_id": self.callback_id,
            "title": {"type": "plain_text", "text": self.title},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Server:* {self.server_name}"},
                },
                {
                    "type": "actions",
                    "block_id": "server_action_block",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": action},
                            "action_id": f"{action.lower()}_server",
                        }
                        for action in self.actions
                    ],
                },
                # remove for now
                # {
                #     "type": "input",
                #     "block_id": "custom_input_block",
                #     "label": {"type": "plain_text", "text": "Custom Command"},
                #     "element": {
                #         "type": "plain_text_input",
                #         "action_id": "custom_command_input",
                #     },
                #     "optional": True,
                # },
                {
                    "type": "actions",
                    "block_id": "custom_action_block",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": self.custom_button_text,
                            },
                            "action_id": "send_custom_command",
                        },
                    ],
                },
            ],
        }
