"""Test for poll workflow functionality."""

import datetime
from unittest.mock import Mock, patch

from friendly_computing_machine.temporal.poll_workflow import (
    PollUpdateActivityParams,
    PollWorkflow,
    PollWorkflowParams,
    finalize_poll_activity,
)


def test_poll_workflow_params():
    """Test PollWorkflowParams dataclass initialization."""
    # Test with default duration
    params = PollWorkflowParams(poll_id=123)
    assert params.poll_id == 123
    assert params.duration_hours == 8

    # Test with custom duration
    params = PollWorkflowParams(poll_id=456, duration_hours=12)
    assert params.poll_id == 456
    assert params.duration_hours == 12


def test_poll_update_activity_params():
    """Test PollUpdateActivityParams dataclass initialization."""
    params = PollUpdateActivityParams(poll_id=789)
    assert params.poll_id == 789


@patch("friendly_computing_machine.temporal.poll_workflow.get_poll_by_id")
@patch("friendly_computing_machine.temporal.poll_workflow.get_poll_options")
@patch("friendly_computing_machine.temporal.poll_workflow.get_poll_vote_counts")
@patch("friendly_computing_machine.temporal.poll_workflow.get_poll_voters_by_option")
@patch("friendly_computing_machine.temporal.poll_workflow.slack_send_message")
def test_update_poll_message_activity_success(
    mock_slack_send, mock_voters, mock_counts, mock_options, mock_get_poll
):
    """Test successful poll message update."""
    # Setup mock data
    mock_poll = Mock()
    mock_poll.id = 1
    mock_poll.title = "Test Poll"
    mock_poll.description = "Test Description"
    mock_poll.slack_channel_slack_id = "C123456"
    mock_poll.slack_message_ts = "1234567890.123456"
    mock_poll.is_active = True
    mock_poll.expires_at = datetime.datetime(2024, 1, 1, 12, 0, 0)

    mock_option1 = Mock()
    mock_option1.id = 1
    mock_option1.text = "Option 1"

    mock_option2 = Mock()
    mock_option2.id = 2
    mock_option2.text = "Option 2"

    mock_get_poll.return_value = mock_poll
    mock_options.return_value = [mock_option1, mock_option2]
    mock_counts.return_value = {1: 3, 2: 1}
    mock_voters.return_value = {1: ["U123", "U456", "U789"], 2: ["U999"]}

    # Test the internal function directly
    from friendly_computing_machine.temporal.poll_workflow import _update_poll_message

    result = _update_poll_message(1)

    # Verify results
    assert result == "Poll message updated successfully"
    mock_get_poll.assert_called_once_with(1)
    mock_options.assert_called_once_with(1)
    mock_counts.assert_called_once_with(1)
    mock_voters.assert_called_once_with(1)
    mock_slack_send.assert_called_once()

    # Verify slack_send_message was called with correct parameters
    call_args = mock_slack_send.call_args
    assert call_args[1]["channel"] == "C123456"
    assert call_args[1]["update_ts"] == "1234567890.123456"
    assert "blocks" in call_args[1]


@patch("friendly_computing_machine.temporal.poll_workflow.get_poll_by_id")
def test_update_poll_message_activity_poll_not_found(mock_get_poll):
    """Test poll message update when poll is not found."""
    mock_get_poll.return_value = None

    from friendly_computing_machine.temporal.poll_workflow import _update_poll_message

    result = _update_poll_message(999)

    assert result == "Poll not found or message not available"
    mock_get_poll.assert_called_once_with(999)


@patch("friendly_computing_machine.temporal.poll_workflow.deactivate_poll")
@patch("friendly_computing_machine.temporal.poll_workflow._update_poll_message")
def test_finalize_poll_activity(mock_update, mock_deactivate):
    """Test poll finalization activity."""
    import asyncio

    async def run_test():
        mock_poll = Mock()
        mock_poll.id = 1
        mock_deactivate.return_value = mock_poll
        mock_update.return_value = "Updated"

        params = PollUpdateActivityParams(poll_id=1)
        result = await finalize_poll_activity(params)

        assert result == "Poll 1 finalized"
        mock_deactivate.assert_called_once_with(1)
        mock_update.assert_called_once_with(1)

    asyncio.run(run_test())

    asyncio.run(run_test())


def test_poll_workflow_initialization():
    """Test that PollWorkflow can be instantiated."""
    workflow = PollWorkflow()
    assert workflow is not None
    assert hasattr(workflow, "update_requested")
    assert workflow.update_requested is False


# Integration test that simulates the workflow pattern
def test_poll_workflow_pattern():
    """Test that the poll workflow follows expected patterns."""
    # Test workflow params validation
    params = PollWorkflowParams(poll_id=1, duration_hours=8)
    assert params.poll_id == 1
    assert params.duration_hours == 8

    # Test activity params validation
    update_params = PollUpdateActivityParams(poll_id=1)
    assert update_params.poll_id == 1

    # Verify workflow class exists and can be instantiated
    workflow = PollWorkflow()
    assert hasattr(workflow, "run")
    assert hasattr(workflow, "request_poll_update")

    # Verify the run method signature accepts the correct parameters
    import inspect

    sig = inspect.signature(workflow.run)
    assert "params" in sig.parameters
    assert sig.parameters["params"].annotation == PollWorkflowParams


def test_poll_workflow_signal():
    """Test that the poll workflow signal handling works."""
    workflow = PollWorkflow()

    # Initially, no update should be requested
    assert workflow.update_requested is False

    # The signal should be an async method
    import asyncio

    async def test_signal():
        await workflow.request_poll_update()
        assert workflow.update_requested is True

    # Run the async test
    asyncio.run(test_signal())
