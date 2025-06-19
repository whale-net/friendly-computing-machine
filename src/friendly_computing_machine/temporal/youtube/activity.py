import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from googleapiclient.discovery import build
from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class YouTubeLiveStreamInfo:
    """Information about a YouTube live stream."""
    
    channel_id: str
    channel_title: str
    video_id: str
    video_title: str
    started_at: datetime


@dataclass
class YouTubeLiveCheckParams:
    """Parameters for checking YouTube live streams."""
    
    channel_ids: List[str]
    minutes_back: int = 2


@activity.defn
async def check_youtube_live_streams_activity(
    params: YouTubeLiveCheckParams
) -> List[YouTubeLiveStreamInfo]:
    """
    Check for YouTube channels that have gone live within the specified time window.
    
    Args:
        params: Parameters containing channel IDs to check and time window
        
    Returns:
        List of live streams that started within the time window
    """
    logger.info(
        "Checking YouTube live streams for %d channels, looking back %d minutes",
        len(params.channel_ids),
        params.minutes_back,
    )
    
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.error("YOUTUBE_API_KEY environment variable not set")
        return []
    
    # Build YouTube API client
    youtube = build("youtube", "v3", developerKey=api_key)
    
    # Calculate time threshold
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=params.minutes_back)
    
    live_streams = []
    
    for channel_id in params.channel_ids:
        try:
            # Search for live streams from this channel
            search_response = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                eventType="live",
                type="video",
                maxResults=5,
            ).execute()
            
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                
                # Get video details to check actual start time
                video_response = youtube.videos().list(
                    part="liveStreamingDetails,snippet",
                    id=video_id,
                ).execute()
                
                if video_response.get("items"):
                    video_info = video_response["items"][0]
                    live_details = video_info.get("liveStreamingDetails", {})
                    
                    # Check if the stream actually started within our time window
                    actual_start_time_str = live_details.get("actualStartTime")
                    if actual_start_time_str:
                        try:
                            actual_start_time = datetime.fromisoformat(
                                actual_start_time_str.replace("Z", "+00:00")
                            )
                            
                            if actual_start_time >= threshold:
                                live_streams.append(
                                    YouTubeLiveStreamInfo(
                                        channel_id=channel_id,
                                        channel_title=item["snippet"]["channelTitle"],
                                        video_id=video_id,
                                        video_title=item["snippet"]["title"],
                                        started_at=actual_start_time,
                                    )
                                )
                                logger.info(
                                    "Found new live stream: %s - %s",
                                    item["snippet"]["channelTitle"],
                                    item["snippet"]["title"],
                                )
                        except ValueError as e:
                            logger.warning(
                                "Failed to parse start time %s: %s",
                                actual_start_time_str,
                                e,
                            )
                            
        except Exception as e:
            logger.error(
                "Error checking channel %s: %s",
                channel_id,
                e,
            )
    
    logger.info("Found %d new live streams", len(live_streams))
    return live_streams


@dataclass
class SlackNotificationParams:
    """Parameters for sending Slack notifications."""
    
    channel: str
    live_streams: List[YouTubeLiveStreamInfo]


@activity.defn
async def send_slack_notification_activity(
    params: SlackNotificationParams
) -> str:
    """
    Send Slack notification for new YouTube live streams.
    
    Args:
        params: Parameters containing Slack channel and live stream info
        
    Returns:
        Status message
    """
    if not params.live_streams:
        logger.info("No live streams to notify about")
        return "No notifications sent - no live streams"
    
    logger.info(
        "Sending Slack notification for %d live streams to channel %s",
        len(params.live_streams),
        params.channel,
    )
    
    try:
        # Import here to avoid dependency issues in workflow sandbox
        from friendly_computing_machine.bot.app import get_slack_web_client
        
        slack_client = get_slack_web_client()
        
        # Create message text
        if len(params.live_streams) == 1:
            stream = params.live_streams[0]
            text = (
                f"🔴 *{stream.channel_title}* just went live!\n"
                f"📺 {stream.video_title}\n"
                f"🔗 https://youtube.com/watch?v={stream.video_id}"
            )
        else:
            text = f"🔴 {len(params.live_streams)} channels just went live!\n\n"
            for stream in params.live_streams:
                text += (
                    f"📺 *{stream.channel_title}*: {stream.video_title}\n"
                    f"🔗 https://youtube.com/watch?v={stream.video_id}\n\n"
                )
        
        # Send message
        response = slack_client.chat_postMessage(
            channel=params.channel,
            text=text,
            unfurl_links=True,
        )
        
        if response["ok"]:
            logger.info("Successfully sent Slack notification")
            return f"Successfully sent notification for {len(params.live_streams)} streams"
        else:
            logger.error("Failed to send Slack notification: %s", response["error"])
            return f"Failed to send notification: {response['error']}"
            
    except Exception as e:
        logger.error("Error sending Slack notification: %s", e)
        return f"Error sending notification: {str(e)}"