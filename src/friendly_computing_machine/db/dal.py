from sqlmodel import select, Session

from typing import Optional
from friendly_computing_machine.db.db import get_session
from friendly_computing_machine.models.slack import (
    SlackChannel,
    SlackUser,
    SlackMessageCreate,
    SlackMessage,
    SlackTeamCreate,
    SlackTeam,
)
from friendly_computing_machine.models.task import TaskCreate, Task, TaskInstanceCreate
# from sqlalchemy.dialects.postgresql import insert

# TODO - move all these into the db equivalents? idk . having one dal (is DAL still a term used to describe this?
#   or too old now? it is still what it claims to be but idk how to best describe it)


def get_music_poll_channel_slack_ids() -> set[str]:
    stmt = select(SlackChannel.slack_id).where(SlackChannel.is_music_poll)
    session = get_session()
    results = session.exec(stmt)
    return {row for row in results}


def get_bot_slack_user_slack_ids() -> set[str]:
    stmt = select(SlackUser.slack_id).where(SlackUser.is_bot)
    session = get_session()
    results = session.exec(stmt)
    return {row for row in results}


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
    session = get_session(session)
    # check if exists and insert. very non-optimal, especially if rbar, but small table so no prob
    stmt = select(Task).where(Task.name == task.name)
    result = session.exec(stmt).one_or_none()
    if result is None:
        result = Task(name=task.name)
        session.add(result)
        session.commit()
        session.refresh(result)

    return result


def insert_task_instances(task_instances: list[TaskInstanceCreate]):
    # no return for now, no need
    session = get_session()
    session.bulk_save_objects([ti.to_task_instance() for ti in task_instances])
    session.commit()


def select_distinct_slack_team_slack_id_from_slack_message() -> set[str]:
    session = get_session()
    # TODO - this will table scan, no index. need to watch out for performance at some far future point
    stmt = select(SlackMessage.slack_team_slack_id).distinct()
    results = session.exec(stmt).all()
    return {row for row in results}


def upsert_slack_teams(slack_teams: list[SlackTeamCreate]) -> list[SlackTeam]:
    # no return, don't care (for now)
    session = get_session()
    out_teams = []
    for slack_team in slack_teams:
        out_teams.append(upsert_slack_team(slack_team, session))
    return out_teams


def upsert_slack_team(
    slack_team: SlackTeamCreate, session: Optional[Session] = None
) -> SlackTeam:
    session = get_session(session)
    # check if exists and insert. very non-optimal, especially if rbar, but small table so no prob
    stmt = select(SlackTeam).where(SlackTeam.slack_id == slack_team.slack_id)
    result = session.exec(stmt).one_or_none()
    if result is None:
        result = slack_team.to_slack_team()
        session.add(result)
        session.commit()
        session.refresh(result)

    return result
