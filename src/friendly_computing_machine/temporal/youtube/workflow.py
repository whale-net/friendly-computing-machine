import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import List

from temporalio import workflow
from temporalio.client import ScheduleIntervalSpec, ScheduleSpec

from friendly_computing_machine.temporal.base import AbstractScheduleWorkflow
from friendly_computing_machine.temporal.youtube.activity import (
    SlackNotificationParams,
    YouTubeLiveCheckParams,
    check_youtube_live_streams_activity,
    send_slack_notification_activity,
)

logger = logging.getLogger(__name__)


@dataclass
class YouTubeLiveWorkflowParams:
    """
    Parameters for the YouTubeLiveWorkflow.
    """
    
    # List of YouTube channel IDs to monitor
    channel_ids: List[str] = None
    # Slack channel to send notifications to
    slack_channel: str = "#general"
    # How many minutes back to check for new live streams
    minutes_back: int = 2
    
    def __post_init__(self):
        if self.channel_ids is None:
            # Hardcoded list of YouTube channel IDs to monitor
            # These are example channel IDs - replace with actual channels to monitor
            self.channel_ids = [
                "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers
                "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed
                "UC8butISFwT-Wl7EV0hUK0BQ",  # Free Code Camp
            ]


@workflow.defn
class YouTubeLiveWorkflow(AbstractScheduleWorkflow):
    """
    Workflow to monitor YouTube channels for new live streams.
    
    This workflow runs every 2 minutes and checks if any monitored channels
    have started live streaming within the last 2 minutes. If so, it sends
    a notification to a Slack channel.
    """

    def get_schedule_spec(self) -> ScheduleSpec:
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))],
        )

    @workflow.run
    async def run(
        self, params: YouTubeLiveWorkflowParams = YouTubeLiveWorkflowParams()
    ):
        logger.info("Starting YouTube live stream check with params: %s", params)

        # Check for new live streams
        live_streams = await workflow.execute_activity(
            check_youtube_live_streams_activity,
            YouTubeLiveCheckParams(
                channel_ids=params.channel_ids,
                minutes_back=params.minutes_back,
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Send Slack notification if there are any new live streams
        if live_streams:
            notification_result = await workflow.execute_activity(
                send_slack_notification_activity,
                SlackNotificationParams(
                    channel=params.slack_channel,
                    live_streams=live_streams,
                ),
                start_to_close_timeout=timedelta(seconds=15),
            )
            
            logger.info("Notification result: %s", notification_result)
            return {
                "live_streams_found": len(live_streams),
                "notification_sent": True,
                "notification_result": notification_result,
            }
        else:
            logger.info("No new live streams found")
            return {
                "live_streams_found": 0,
                "notification_sent": False,
                "notification_result": "No live streams to notify about",
            }