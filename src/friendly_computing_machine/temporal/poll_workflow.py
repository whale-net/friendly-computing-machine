import logging
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow

from friendly_computing_machine.bot.util import slack_send_message
from friendly_computing_machine.db.dal.poll_dal import (
    deactivate_poll,
    get_poll_by_id,
    get_poll_options,
    get_poll_vote_counts,
    get_poll_voters_by_option,
)

logger = logging.getLogger(__name__)


@dataclass
class PollWorkflowParams:
    poll_id: int
    duration_hours: int = 8


@dataclass
class PollUpdateActivityParams:
    poll_id: int


@activity.defn
async def update_poll_message_activity(params: PollUpdateActivityParams) -> str:
    """Activity to update the poll message with current vote counts."""
    return _update_poll_message(params.poll_id)


def _update_poll_message(poll_id: int) -> str:
    """Internal function to update poll message - can be called from activities or directly."""
    poll = get_poll_by_id(poll_id)
    if not poll or not poll.slack_message_ts:
        return "Poll not found or message not available"

    options = get_poll_options(poll_id)
    vote_counts = get_poll_vote_counts(poll_id)
    voters_by_option = get_poll_voters_by_option(poll_id)

    # Build poll message content
    message_blocks = []

    # Poll title and description
    title_text = f"📊 **{poll.title}**"
    if poll.description:
        title_text += f"\n_{poll.description}_"

    message_blocks.append(
        {"type": "section", "text": {"type": "mrkdwn", "text": title_text}}
    )

    # Poll status
    if poll.is_active:
        status_text = (
            f"🟢 *Active until* {poll.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
    else:
        status_text = "🔴 *Poll Closed*"

    message_blocks.append(
        {"type": "section", "text": {"type": "mrkdwn", "text": status_text}}
    )

    message_blocks.append({"type": "divider"})

    # Poll options with vote counts and voting buttons
    for option in options:
        vote_count = vote_counts.get(option.id, 0)
        voters = voters_by_option.get(option.id, [])

        # Create voter display (limit to first 10, then show count)
        voter_display = ""
        if voters:
            if len(voters) <= 10:
                voter_display = " • " + ", ".join([f"<@{voter}>" for voter in voters])
            else:
                first_voters = ", ".join([f"<@{voter}>" for voter in voters[:10]])
                voter_display = f" • {first_voters} and {len(voters) - 10} more"

        option_text = f"*{option.text}* ({vote_count} vote{'s' if vote_count != 1 else ''}){voter_display}"

        block = {"type": "section", "text": {"type": "mrkdwn", "text": option_text}}

        # Add vote button if poll is active
        if poll.is_active:
            block["accessory"] = {
                "type": "button",
                "text": {"type": "plain_text", "text": "Vote"},
                "action_id": f"poll_vote_{poll.id}_{option.id}",
                "value": f"{poll.id}_{option.id}",
            }

        message_blocks.append(block)

    # Update the message
    try:
        slack_send_message(
            channel=poll.slack_channel_slack_id,
            blocks=message_blocks,
            update_ts=poll.slack_message_ts,
        )
        return "Poll message updated successfully"
    except Exception as e:
        logger.error(f"Failed to update poll message: {e}")
        return f"Failed to update poll message: {str(e)}"


@activity.defn
async def finalize_poll_activity(params: PollUpdateActivityParams) -> str:
    """Activity to finalize a poll when it expires."""
    poll = deactivate_poll(params.poll_id)

    # Update the message one final time to show final results
    _update_poll_message(params.poll_id)

    return f"Poll {poll.id} finalized"


@workflow.defn
class PollWorkflow:
    """Temporal workflow to manage a poll lifecycle."""

    def __init__(self):
        self.update_requested = False

    @workflow.signal
    async def request_poll_update(self):
        """Signal to request a poll message update."""
        self.update_requested = True

    @workflow.run
    async def run(self, params: PollWorkflowParams) -> str:
        """Run the poll workflow for the specified duration."""
        logger.info(f"Starting poll workflow for poll {params.poll_id}")

        # Update poll message immediately
        await workflow.execute_activity(
            update_poll_message_activity,
            PollUpdateActivityParams(poll_id=params.poll_id),
            start_to_close_timeout=timedelta(seconds=30),
        )

        poll_duration = timedelta(hours=params.duration_hours)
        end_time = workflow.now() + poll_duration

        # Wait for either poll expiration or signals
        while workflow.now() < end_time:
            # Calculate remaining time
            remaining_time = end_time - workflow.now()

            # Wait for either a signal or timeout (remaining time)
            try:
                await workflow.wait_condition(
                    lambda: self.update_requested, timeout=remaining_time
                )
            except Exception:
                # Timeout occurred, poll has expired
                logger.info(f"Poll {params.poll_id} has expired")
                break

            # If we got here, it means we received an update signal
            if self.update_requested:
                self.update_requested = False
                logger.info(f"Received update signal for poll {params.poll_id}")

                # Update the poll message
                try:
                    await workflow.execute_activity(
                        update_poll_message_activity,
                        PollUpdateActivityParams(poll_id=params.poll_id),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to update poll message during workflow: {e}"
                    )

        # Finalize the poll
        result = await workflow.execute_activity(
            finalize_poll_activity,
            PollUpdateActivityParams(poll_id=params.poll_id),
            start_to_close_timeout=timedelta(seconds=30),
        )

        logger.info(f"Poll workflow completed for poll {params.poll_id}")
        return result
