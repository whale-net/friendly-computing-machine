"""Slack block models using slack_bolt/slack_sdk components."""

from typing import List

from slack_sdk.models.blocks import (
    ActionsBlock,
    ButtonElement,
    DividerBlock,
    PlainTextObject,
    SectionBlock,
)


def create_worker_status_blocks(
    friendly_name: str, name: str, id: str, current_status: str
) -> List:
    """
    Create a block payload for worker status display.

    Args:
        friendly_name: The friendly display name of the worker
        name: The worker name
        id: The worker ID
        current_status: The current status of the worker

    Returns:
        List of Slack blocks representing the worker status message
    """
    return [
        SectionBlock(
            text={
                "type": "mrkdwn",
                "text": f":satellite_antenna: {friendly_name} ({name} {id})",
            }
        ),
        DividerBlock(),
        SectionBlock(
            text={"type": "plain_text", "text": f"current_status: {current_status}"}
        ),
        ActionsBlock(
            elements=[
                # TODO - confirmation dialog for stop
                ButtonElement(
                    text=PlainTextObject(text="Stop", emoji=True),
                    style="danger",
                    value=id,
                    action_id="worker-stop",
                )
            ]
        ),
    ]
