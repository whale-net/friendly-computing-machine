from sqlmodel import select, Session

from typing import Optional
from friendly_computing_machine.db.db import get_session
from friendly_computing_machine.models.slack import (
    SlackChannel,
    SlackUser,
    SlackUserCreate,
    SlackMessageCreate,
    SlackMessage,
    SlackTeamCreate,
    SlackTeam,
)
from friendly_computing_machine.models.task import (
    TaskCreate,
    Task,
    TaskInstanceCreate,
    TaskInstance,
    TaskInstanceStatus,
)


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


def upsert_task(task: TaskCreate, session: Optional[Session] = None) -> Task:
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
    # print(f'{len(task_instances)} inserted')
    session.commit()


def select_distinct_slack_team_slack_id_from_slack_message() -> set[str]:
    session = get_session()
    # TODO - this will table scan, no index. need to watch out for performance at some far future point
    stmt = select(SlackMessage.slack_team_slack_id).distinct()
    results = session.exec(stmt).all()
    return {row for row in results}


def upsert_slack_teams(slack_teams: list[SlackTeamCreate]) -> list[SlackTeam]:
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


def get_slack_teams(session: Optional[Session] = None) -> list[SlackTeam]:
    session = get_session(session)
    stmt = select(SlackTeam)
    return list(session.exec(stmt).all())


def get_slack_team_id_map(session: Optional[Session] = None) -> dict[str, int]:
    slack_teams = get_slack_teams(session)
    return {slack_team.slack_id: slack_team.id for slack_team in slack_teams}


def get_user_teams_from_messages(slack_team_slack_id: str) -> set[tuple[str, str]]:
    session = get_session()
    # TODO - this will table scan, no index. need to watch out for performance at some far future point
    stmt = (
        select(SlackMessage.slack_user_slack_id, SlackMessage.slack_team_slack_id)
        .where(SlackMessage.slack_team_slack_id == slack_team_slack_id)
        .distinct()
    )
    results = session.exec(stmt).all()
    return {(row.slack_user_slack_id, row.slack_team_slack_id) for row in results}


def upsert_slack_users(slack_users: list[SlackUserCreate]) -> list[SlackUser]:
    session = get_session()
    out_users = []
    slack_team_id_map = get_slack_team_id_map(session)
    for slack_user in slack_users:
        out_users.append(
            upsert_slack_user(
                slack_user, session=session, slack_team_id_map=slack_team_id_map
            )
        )
    return out_users


def upsert_slack_user(
    slack_user: SlackUserCreate,
    session: Optional[Session] = None,
    slack_team_id_map: Optional[dict[str, int]] = None,
) -> SlackUser:
    # this code sucks, should rewrite

    session = get_session(session)

    if slack_team_id_map is None:
        slack_team_id_map = get_slack_team_id_map(session)
    slack_team_id = slack_team_id_map.get(slack_user.slack_team_slack_id)

    # check if exists. very non-optimal, especially if rbar, but small table so no prob
    stmt = select(SlackUser).where(SlackUser.slack_id == slack_user.slack_id)
    result = session.exec(stmt).one_or_none()
    if result is None:
        user = slack_user.to_slack_user(slack_team_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        result = user
    elif (
        result.name == slack_user.name
        # these aren't expected to change but keeping for consistency
        or result.slack_team_slack_id != slack_user.slack_team_slack_id
        or result.slack_team_id != slack_team_id
    ):
        # TODO - pydantic idiomatic way of doing this
        result.name = slack_user.name
        result.slack_team_slack_id = slack_user.slack_team_slack_id
        result.slack_team_id = slack_team_id

        session.add(result)
        session.commit()
        session.refresh(result)

    return result


def get_last_successful_task_instance(task: Task) -> TaskInstance | None:
    session = get_session()
    stmt = (
        select(TaskInstance)
        .where(
            TaskInstance.task_id == task.id
            and TaskInstance.status == TaskInstanceStatus.OK
        )
        .order_by(TaskInstance.as_of.desc())
        .limit(1)
    )
    return session.exec(stmt).one_or_none()
