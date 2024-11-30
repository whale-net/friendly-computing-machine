from friendly_computing_machine.util import ts_to_datetime
from friendly_computing_machine.models.slack import SlackMessageCreate
from friendly_computing_machine.bot.main import app, get_bot_config
from friendly_computing_machine.db.dal import insert_message


@app.event("message")
def handle_message(event, say):
    # TODO: typehint for event? or am I supposed to just yolo it?
    # TODO: logging
    print("event")
    try:
        message = SlackMessageCreate(
            slack_id=event.get("client_msg_id"),
            slack_team_slack_id=event.get("team"),
            slack_channel_slack_id=event.get("channel"),  #
            slack_user_slack_id=event.get("user"),
            text=event.get("text"),
            ts=ts_to_datetime(event.get("ts")),
            thread_ts=event.get("thread_ts"),
            parent_user_slack_id=event.get("parent_user_id"),
        )
        print(event)

        # Rules for inserting messages
        # is in channel.is_music_poll
        # and
        # (
        #   is from bot user
        #   or
        #   is message in thread from bot user
        # )
        config = get_bot_config()

        # demorgans the above
        if message.slack_channel_slack_id not in config.MUSIC_POLL_CHANNEL_IDS:
            print(f"skipping message {message.slack_id} - not in music poll channel")
            return
        elif (
            message.slack_user_slack_id not in config.BOT_SLACK_USER_IDS
            and message.parent_user_slack_id not in config.BOT_SLACK_USER_IDS
        ):
            print(
                f"skipping message {message.slack_id} - not posted by bot user, or in bot user thread"
            )
            return

        # if we reach this point, we can insert the message
        # will be processed later
        msg = insert_message(message)
        print(f"message inserted: {msg}")
    except Exception as e:
        print(f"exception encountered: {e}")
        raise
