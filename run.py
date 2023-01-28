import logging
import os

# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# WebClient instantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.


def get_date_from_ts(ts):
    ts = float(ts)
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S.%f")


def get_conversation_id(web_client: WebClient, channel_name: str):
    # try:
    # Call the conversations.list method using the WebClient
    for result in web_client.conversations_list():
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    # except SlackApiError as e:
    #     print(f"Error: {e}")


def get_conversation_history(web_client: WebClient, conversation_id: str):
    result = web_client.conversations_history(channel=conversation_id)
    return result["messages"]


def get_all_messages_str(web_client: WebClient, conversation_id: str):
    history = get_conversation_history(web_client, conversation_id)
    # history_size = len(history) + sum(map(lambda x : x['reply_count'] if 'reply_count' in x.keys() else 0, history))

    def format_message(msg: dict, is_reply: bool = False):
        msg_ts = get_date_from_ts(msg.get("ts"))
        msg_type = msg.get("type")
        msg_subtype = msg.get("subtype") or "generic"
        msg_user = msg.get("user") or "system"
        msg_text = msg.get("text") or ""

        msg_thread_ts = msg.get("thread_ts")
        # this is bad
        msg_text = msg_text + ("(msg has file(s))" if msg.get("files") else "")

        msg_prefix = "--->" if is_reply else ""

        return (
            f"{msg_prefix}[{msg_ts}]@{msg_type}.{msg_subtype} [{msg_user}]: {msg_text}"
        )

    out_message_str = []
    for message in history:
        out_message_str.append(format_message(message))
        thread_ts = message.get("thread_ts")
        if thread_ts:
            reply_result = web_client.conversations_replies(
                channel=conversation_id, ts=thread_ts
            )
            for reply_message in reply_result.data["messages"]:
                out_message_str.append(format_message(reply_message, is_reply=True))

    return out_message_str

    # for msg in history


if __name__ == "__main__":
    web_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
    logger = logging.getLogger(__name__)

    conversation_id = get_conversation_id(web_client, "testing-app")
    message_strs = get_all_messages_str(web_client, conversation_id)
    message_strs.reverse()
    for msg in message_strs:
        print(msg)
