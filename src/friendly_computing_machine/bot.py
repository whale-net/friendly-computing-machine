import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Initializes your app with your bot token and socket mode handler

# it is stupid as hell but I guess I need to create this out here with a token from env
# It does not seem possible to create it here, use for decorators, and then authenticate during runtime
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


# Start your app
def run_slack_bot(app_token: str):  # ), bot_token: str):
    SocketModeHandler(app, app_token).start()


# TODO - eventually make this dynamic
MUSIC_POLL_CHANNEL_IDS: set[str] = {"C0805L9310S"}


@app.event("message")
def handle_message(event, say):
    print(event)
