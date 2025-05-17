from dataclasses import dataclass, field
from typing import List

# Import necessary components from slack_sdk
from slack_sdk.models.blocks import (
    ActionsBlock,
    ButtonElement,
    InputBlock,
    MarkdownTextObject,
    Option,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
)
from slack_sdk.models.views import View

# ServerOption class is removed as it's replaced by slack_sdk.models.blocks.Option


@dataclass
class ServerSelectModal:
    options: List[Option]  # Use slack_sdk Option
    callback_id: str = "server_select_modal"
    title: str = "Select Server"
    submit_text: str = "Next"

    def build(self) -> View:  # Return a slack_sdk View object
        return View(
            type="modal",
            callback_id=self.callback_id,
            title=PlainTextObject(text=self.title),
            submit=PlainTextObject(text=self.submit_text),
            blocks=[
                InputBlock(
                    block_id="server_select_block",
                    label=PlainTextObject(text="Choose a server"),
                    element=StaticSelectElement(
                        action_id="server_select_action",
                        placeholder=PlainTextObject(text="Select a server"),
                        options=self.options,  # Directly use the list of Option objects
                    ),
                )
            ],
        )


@dataclass
class ServerActionModal:
    server_name: str
    callback_id: str = "server_action_modal"
    title: str = "Server Actions"
    actions: List[str] = field(default_factory=lambda: ["Start", "Stop", "Restart"])
    custom_button_text: str = "Send Custom"

    def build(self) -> View:  # Return a slack_sdk View object
        # No submit button needed for an action-only modal typically
        return View(
            type="modal",
            callback_id=self.callback_id,
            title=PlainTextObject(text=self.title),
            # close=PlainTextObject(text="Cancel"), # Example: Add a close button if needed
            blocks=[
                SectionBlock(
                    text=MarkdownTextObject(text=f"*Server:* {self.server_name}")
                ),
                ActionsBlock(
                    block_id="server_action_block",
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text=action),
                            action_id=f"{action.lower()}_server",
                            value=action.lower(),  # Pass action as value if needed
                        )
                        for action in self.actions
                    ],
                ),
                # InputBlock(
                #     block_id="custom_input_block",
                #     label=PlainTextObject(text="Custom Command"),
                #     element=PlainTextInputElement(action_id="custom_command_input"),
                #     optional=True,
                # ),
                ActionsBlock(
                    block_id="custom_action_block",
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text=self.custom_button_text),
                            action_id="send_custom_command",
                        ),
                    ],
                ),
            ],
        )
