from sqlalchemy import select

from friendly_computing_machine.db.db import get_session
from friendly_computing_machine.models.slack import (
    SlackChannel,
    SlackUser,
    SlackMessageCreate,
    SlackMessage,
)


def get_music_poll_channel_slack_ids() -> set[str]:
    ids = set()
    stmt = select(SlackChannel.slack_id).where(SlackChannel.is_music_poll)
    session = get_session()
    result = session.exec(stmt)
    for row in result:
        ids.add(row.slack_id)
    return ids


def get_bot_slack_user_slack_ids() -> set[str]:
    ids = set()
    stmt = select(SlackUser.slack_id).where(SlackUser.is_bot)
    session = get_session()
    result = session.exec(stmt)
    for row in result:
        ids.add(row.slack_id)
    return ids


def insert_message(in_message: SlackMessageCreate) -> SlackMessage:
    message = SlackMessage(
        slack_id=in_message.slack_id,
        slack_team_slack_id=in_message.slack_team_slack_id,
        slack_channel_slack_id=in_message.slack_channel_slack_id,
        slack_user_slack_id=in_message.slack_user_slack_id,
        text=in_message.text,
        ts=in_message.ts,
        thread_ts=in_message.thread_ts,
        parent_user_slack_id=in_message.parent_user_slack_id,
    )
    session = get_session()
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
