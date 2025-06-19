"""Test YouTube live workflow components."""

import pytest
from datetime import datetime, timezone
from friendly_computing_machine.temporal.youtube.activity import (
    YouTubeLiveStreamInfo,
    YouTubeLiveCheckParams,
    SlackNotificationParams,
)
from friendly_computing_machine.temporal.youtube.workflow import (
    YouTubeLiveWorkflow,
    YouTubeLiveWorkflowParams,
)


def test_youtube_live_stream_info_creation():
    """Test that YouTubeLiveStreamInfo can be created."""
    info = YouTubeLiveStreamInfo(
        channel_id="test_channel",
        channel_title="Test Channel",
        video_id="test_video",
        video_title="Test Stream",
        started_at=datetime.now(timezone.utc),
    )
    
    assert info.channel_id == "test_channel"
    assert info.channel_title == "Test Channel"
    assert info.video_id == "test_video"
    assert info.video_title == "Test Stream"
    assert isinstance(info.started_at, datetime)


def test_youtube_live_check_params():
    """Test YouTubeLiveCheckParams creation and defaults."""
    params = YouTubeLiveCheckParams(channel_ids=["test1", "test2"])
    
    assert params.channel_ids == ["test1", "test2"]
    assert params.minutes_back == 2  # default value
    assert params.scheduled_time is None  # default value
    
    # Test with custom minutes_back
    params_custom = YouTubeLiveCheckParams(
        channel_ids=["test1"], 
        minutes_back=5
    )
    assert params_custom.minutes_back == 5
    assert params_custom.scheduled_time is None
    
    # Test with scheduled_time
    scheduled_time = datetime.now(timezone.utc)
    params_with_time = YouTubeLiveCheckParams(
        channel_ids=["test1"],
        scheduled_time=scheduled_time,
    )
    assert params_with_time.scheduled_time == scheduled_time


def test_slack_notification_params():
    """Test SlackNotificationParams creation."""
    stream_info = YouTubeLiveStreamInfo(
        channel_id="test_channel",
        channel_title="Test Channel", 
        video_id="test_video",
        video_title="Test Stream",
        started_at=datetime.now(timezone.utc),
    )
    
    params = SlackNotificationParams(
        channel="#test",
        live_streams=[stream_info],
    )
    
    assert params.channel == "#test"
    assert len(params.live_streams) == 1
    assert params.live_streams[0] == stream_info


def test_youtube_live_workflow_params():
    """Test YouTubeLiveWorkflowParams creation and defaults."""
    # Test with defaults
    params = YouTubeLiveWorkflowParams()
    
    assert params.slack_channel == "#general"
    assert params.minutes_back == 2
    assert isinstance(params.channel_ids, list)
    assert len(params.channel_ids) > 0  # Should have default channels
    
    # Test with custom values
    custom_params = YouTubeLiveWorkflowParams(
        channel_ids=["custom1", "custom2"],
        slack_channel="#custom",
        minutes_back=5,
    )
    
    assert custom_params.channel_ids == ["custom1", "custom2"]
    assert custom_params.slack_channel == "#custom"
    assert custom_params.minutes_back == 5


def test_youtube_live_workflow_schedule():
    """Test that YouTubeLiveWorkflow has the correct schedule."""
    workflow = YouTubeLiveWorkflow()
    schedule_spec = workflow.get_schedule_spec()
    
    # Should run every 2 minutes
    assert len(schedule_spec.intervals) == 1
    interval = schedule_spec.intervals[0]
    assert interval.every.total_seconds() == 120  # 2 minutes in seconds