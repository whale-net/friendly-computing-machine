from sqlmodel import select, Session

from typing import Optional
from friendly_computing_machine.db.db import get_session
from friendly_computing_machine.models.slack import (
    SlackChannel,
    SlackUser,
    SlackMessageCreate,
    SlackMessage,
)
from friendly_computing_machine.models.task import TaskCreate, Task
# from sqlalchemy.dialects.postgresql import insert

# TODO - move all these into the db equivalents? idk . having one dal (is DAL still a term used to describe this?
#   or too old now? it is still what it claims to be but idk how to best describe it)


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


def upsert_tasks(tasks: list[TaskCreate]) -> list[Task]:
    # RBAR BABY
    # I tried to look into upserts with sa, but didn't want to rabbit hole myself for minimal gain here
    session = get_session()
    out_tasks = []
    for task in tasks:
        out_tasks.append(upsert_task(task, session))
    return list(out_tasks)


def upsert_task(task: TaskCreate, session: Optional[Session]) -> Task:
    if session is None:
        session = get_session()

    # check if exists and insert. very non-optimal, especially if rbar, but small table so no prob
    stmt = select(Task).where(Task.name == task.name)
    result = session.exec(stmt).one_or_none()
    if result is None:
        result = Task(name=task.name)
        session.add(result)
        session.commit()
        session.refresh(result)

    return result
