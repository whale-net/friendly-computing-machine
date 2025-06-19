# YouTube Live Stream Monitor

This temporal workflow monitors YouTube channels for new live streams and sends Slack notifications when channels go live.

## Features

- Runs every 2 minutes automatically
- Checks for channels that went live within the last 2 minutes 
- Sends formatted Slack notifications with stream details
- Configurable channel list and Slack destination
- Handles multiple concurrent live streams

## Configuration

### Environment Variables

- `YOUTUBE_API_KEY`: Required. YouTube Data API v3 key for accessing live stream data.
  - Get one from [Google Cloud Console](https://console.cloud.google.com/)
  - Enable the YouTube Data API v3
  - Create credentials for your application

### Default Settings

The workflow comes with hardcoded defaults that can be overridden:

```python
# Default YouTube channels monitored (example channels)
channel_ids = [
    "UC_x5XG1OV2P6uZZ5FSM9Ttw",  # Google Developers
    "UCsooa4yRKGN_zEE8iknghZA",  # TED-Ed  
    "UC8butISFwT-Wl7EV0hUK0BQ",  # Free Code Camp
]

# Default Slack channel
slack_channel = "#general"

# Default time window
minutes_back = 2
```

### Customizing Channels

To monitor different YouTube channels, update the `channel_ids` in `YouTubeLiveWorkflowParams`:

1. Find the channel ID from the YouTube channel URL or API
2. Add to the default list in `workflow.py`, or
3. Pass custom parameters when starting the workflow

## How It Works

1. **Schedule**: Temporal automatically runs the workflow every 2 minutes
2. **Check**: The `check_youtube_live_streams_activity` queries YouTube API for each monitored channel
3. **Filter**: Only streams that started within the last 2 minutes are considered "new"
4. **Notify**: The `send_slack_notification_activity` formats and sends Slack messages
5. **Result**: Returns summary of streams found and notification status

## Message Format

Single stream:
```
🔴 *Channel Name* just went live!
📺 Stream Title
🔗 https://youtube.com/watch?v=VIDEO_ID
```

Multiple streams:
```
🔴 3 channels just went live!

📺 *Channel 1*: Stream Title 1
🔗 https://youtube.com/watch?v=VIDEO_ID_1

📺 *Channel 2*: Stream Title 2  
🔗 https://youtube.com/watch?v=VIDEO_ID_2
```

## Development

### Testing

Run the tests to validate the workflow components:

```bash
python -m pytest tests/test_youtube_workflow.py -v
```

### Adding to Worker

The workflow is automatically registered in `temporal/worker.py`:

```python
from friendly_computing_machine.temporal.youtube.workflow import YouTubeLiveWorkflow
from friendly_computing_machine.temporal.youtube.activity import (
    check_youtube_live_streams_activity,
    send_slack_notification_activity,
)

WORKFLOWS = [..., YouTubeLiveWorkflow]
ACTIVITIES = [..., check_youtube_live_streams_activity, send_slack_notification_activity]
```

## Error Handling

- Missing API key: Logs error and returns empty results
- API failures: Logs errors per channel, continues with other channels  
- Slack failures: Logs error and returns failure status
- Network issues: Temporal will retry according to configured retry policies

## API Limits

YouTube Data API v3 has quotas:
- 10,000 quota units per day by default
- Search costs ~100 units per request
- Video details cost ~1 unit per request

With default settings (3 channels, every 2 minutes):
- ~2,160 requests per day
- ~216,000 quota units per day
- You may need to request quota increase for production use