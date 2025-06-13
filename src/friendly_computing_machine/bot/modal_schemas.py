from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

# Import necessary components from slack_sdk
from slack_sdk.models.blocks import (
    ActionsBlock,
    ButtonElement,
    InputBlock,
    MarkdownTextObject,
    Option,
    PlainTextInputElement,
    PlainTextObject,
    SectionBlock,
    StaticSelectElement,
)
from slack_sdk.models.views import View

# ServerOption class is removed as it's replaced by slack_sdk.models.blocks.Option


class BaseModalView(ABC):
    """Abstract base class for modal views in the Slack application.

    This class defines the common interface for all modal views and ensures
    they all implement the necessary methods for building views.
    """

    callback_id: str
    title: str

    @abstractmethod
    def build(self) -> View:
        """Build and return a Slack View object.

        This method must be implemented by all subclasses.

        Returns:
            View: A fully constructed Slack View object
        """
        pass


@dataclass
class ServerSelectModal(BaseModalView):
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
                # TODO - use ActionsBlock with LinkButtonElement to list servers and avoid ddl
            ],
        )


@dataclass
class ServerActionModal(BaseModalView):
    server_name: str
    callback_id: str = "server_action_modal"
    title: str = "Server Actions"
    actions: List[str] = field(default_factory=lambda: ["Start", "Stop", "Restart"])
    custom_button_text: str = "Send Custom"

    def build(
        self, game_server_instance_id: int
    ) -> View:  # Return a slack_sdk View object
        # No submit button needed for an action-only modal typically
        return View(
            type="modal",
            private_metadata=str(game_server_instance_id),
            callback_id=self.callback_id,
            title=PlainTextObject(text=self.title),
            # close=PlainTextObject(text="Cancel"), # Example: Add a close button if needed
            # just use close for submit
            submit=PlainTextObject(text="Close (but green)", emoji=True),
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
                InputBlock(
                    block_id="stdin_custom_input_block",
                    label=PlainTextObject(
                        text="Send a Command to the Server's Admin Console"
                    ),
                    element=PlainTextInputElement(
                        action_id="stdin_custom_command_input"
                    ),
                    optional=True,
                ),
                ActionsBlock(
                    block_id="custom_action_block",
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text=self.custom_button_text),
                            action_id="send_stdin_custom_command",
                        ),
                    ],
                ),
            ],
        )


@dataclass
class PollCreateModal(BaseModalView):
    callback_id: str = "poll_create_modal"
    title: str = "Create Poll"
    submit_text: str = "Create Poll"

    def build(self) -> View:
        return View(
            type="modal",
            callback_id=self.callback_id,
            title=PlainTextObject(text=self.title),
            submit=PlainTextObject(text=self.submit_text),
            blocks=[
                InputBlock(
                    block_id="poll_title_block",
                    label=PlainTextObject(text="Poll Title"),
                    element=PlainTextInputElement(
                        action_id="poll_title_input",
                        placeholder=PlainTextObject(text="Enter poll title"),
                        max_length=255,
                    ),
                ),
                InputBlock(
                    block_id="poll_description_block",
                    label=PlainTextObject(text="Poll Description (Optional)"),
                    element=PlainTextInputElement(
                        action_id="poll_description_input",
                        placeholder=PlainTextObject(text="Enter poll description"),
                        multiline=True,
                        max_length=1000,
                    ),
                    optional=True,
                ),
                InputBlock(
                    block_id="poll_option_1_block",
                    label=PlainTextObject(text="Option 1"),
                    element=PlainTextInputElement(
                        action_id="poll_option_1_input",
                        placeholder=PlainTextObject(text="Enter first option"),
                        max_length=255,
                    ),
                ),
                InputBlock(
                    block_id="poll_option_2_block",
                    label=PlainTextObject(text="Option 2"),
                    element=PlainTextInputElement(
                        action_id="poll_option_2_input",
                        placeholder=PlainTextObject(text="Enter second option"),
                        max_length=255,
                    ),
                ),
                InputBlock(
                    block_id="poll_option_3_block",
                    label=PlainTextObject(text="Option 3 (Optional)"),
                    element=PlainTextInputElement(
                        action_id="poll_option_3_input",
                        placeholder=PlainTextObject(text="Enter third option"),
                        max_length=255,
                    ),
                    optional=True,
                ),
                InputBlock(
                    block_id="poll_option_4_block",
                    label=PlainTextObject(text="Option 4 (Optional)"),
                    element=PlainTextInputElement(
                        action_id="poll_option_4_input",
                        placeholder=PlainTextObject(text="Enter fourth option"),
                        max_length=255,
                    ),
                    optional=True,
                ),
                InputBlock(
                    block_id="poll_option_5_block",
                    label=PlainTextObject(text="Option 5 (Optional)"),
                    element=PlainTextInputElement(
                        action_id="poll_option_5_input",
                        placeholder=PlainTextObject(text="Enter fifth option"),
                        max_length=255,
                    ),
                    optional=True,
                ),
            ],
        )
