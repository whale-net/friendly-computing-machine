import logging
import datetime
from typing import Optional

from sqlmodel import Session, and_, column, null, select, update

from friendly_computing_machine.db.db import SessionManager
from friendly_computing_machine.models.slack import (
    SlackChannel,
    SlackMessage,
    SlackMessageCreate,
    SlackTeam,
    SlackTeamCreate,
    SlackUser,
    SlackUserCreate,
)
from friendly_computing_machine.models.genai import (
    GenAIText,
    GenAITextCreate,
)
from friendly_computing_machine.models.task import (
    Task,
    TaskCreate,
    TaskInstance,
    TaskInstanceCreate,
    TaskInstanceStatus,
)
from friendly_computing_machine.models.music_poll import (
    MusicPoll,
    MusicPollCreate,
    MusicPollInstance,
    MusicPollInstanceCreate,
    MusicPollResponse,
    MusicPollResponseCreate,
)
from friendly_computing_machine.db.util import db_update

logger = logging.getLogger(__name__)

# from sqlalchemy.dialects.postgresql import insert

# TODO - move all these into the db equivalents? idk . having one dal (is DAL still a term used to describe this?
#   or too old now? it is still what it claims to be but idk how to best describe it)


def get_music_poll_channel_slack_ids() -> set[str]:
    stmt = select(SlackChannel.slack_id).join(
        MusicPoll, MusicPoll.slack_channel_id == SlackChannel.id
    )
    with SessionManager() as session:
        results = session.exec(stmt)
    return {row for row in results}


def get_bot_slack_user_slack_ids() -> set[str]:
    stmt = select(SlackUser.slack_id).where(SlackUser.is_bot)
    with SessionManager() as session:
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
    with SessionManager() as session:
        session.add(message)
        session.commit()
        # TODO - does return after refresh cause any issues?
        # I remember this being problematic at some point but maybe I was doing something wrong then
        session.refresh(message)
    return message


def upsert_tasks(tasks: list[TaskCreate]) -> list[Task]:
    # RBAR BABY
    # I tried to look into upserts with sa, but didn't want to rabbit hole myself for minimal gain here
    with SessionManager() as session:
        out_tasks = []
        for task in tasks:
            out_tasks.append(upsert_task(task, session))
    return list(out_tasks)


def upsert_task(task: TaskCreate, session: Optional[Session] = None) -> Task:
    with SessionManager(session) as session:
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
    with SessionManager() as session:
        session.bulk_save_objects([ti.to_task_instance() for ti in task_instances])
        # print(f'{len(task_instances)} inserted')
        session.commit()


def select_distinct_slack_team_slack_id_from_slack_message() -> set[str]:
    with SessionManager() as session:
        # TODO - this will table scan, no index. need to watch out for performance at some far future point
        stmt = select(SlackMessage.slack_team_slack_id).distinct()
        results = session.exec(stmt).all()
    return {row for row in results}


def upsert_slack_teams(slack_teams: list[SlackTeamCreate]) -> list[SlackTeam]:
    with SessionManager() as session:
        out_teams = []
        for slack_team in slack_teams:
            out_teams.append(upsert_slack_team(slack_team, session))
    return out_teams


def upsert_slack_team(
    slack_team: SlackTeamCreate, session: Optional[Session] = None
) -> SlackTeam:
    with SessionManager() as session:
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
    with SessionManager(session) as session:
        stmt = select(SlackTeam)
        return list(session.exec(stmt).all())


def get_slack_team_id_map(session: Optional[Session] = None) -> dict[str, int]:
    with SessionManager(session) as session:
        slack_teams = get_slack_teams(session)
    return {slack_team.slack_id: slack_team.id for slack_team in slack_teams}


def get_user_teams_from_messages(slack_team_slack_id: str) -> set[tuple[str, str]]:
    with SessionManager() as session:
        # TODO - this will table scan, no index. need to watch out for performance at some far future point
        stmt = (
            select(SlackMessage.slack_user_slack_id, SlackMessage.slack_team_slack_id)
            .where(SlackMessage.slack_team_slack_id == slack_team_slack_id)
            .distinct()
        )
        results = session.exec(stmt).all()
    return {(row.slack_user_slack_id, row.slack_team_slack_id) for row in results}


def upsert_slack_users(slack_users: list[SlackUserCreate]) -> list[SlackUser]:
    out_users = []
    with SessionManager() as session:
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
    # TODO this code sucks, should rewrite

    with SessionManager(session) as session:
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
    with SessionManager() as session:
        stmt = (
            select(TaskInstance)
            .where(
                and_(
                    TaskInstance.task_id == task.id,
                    TaskInstance.status == TaskInstanceStatus.OK.name,
                )
            )
            .order_by(TaskInstance.as_of.desc())
            .limit(1)
        )
        return session.exec(stmt).one_or_none()


def backfill_slack_messages_slack_user_id():
    with SessionManager() as session:
        stmt = (
            update(SlackMessage)
            .where(column("slack_user_id").is_(null()))
            .values(
                slack_user_id=(
                    select(SlackUser.id)
                    # no index, but should be fine due to low table size
                    .where(SlackUser.slack_id == SlackMessage.slack_user_slack_id)
                    .limit(1)
                    .scalar_subquery()
                )
            )
        )
        session.exec(stmt)
        session.commit()
        # not done - slack_parent_user_id

        # just want some logs for now. not going to retrofit everything in this file for logging
        logger.info("backfill_slack_messages_slack_user_id complete")


def backfill_slack_messages_slack_channel_id():
    with SessionManager() as session:
        stmt = (
            update(SlackMessage)
            .where(column("slack_channel_id").is_(null()))
            .values(
                slack_channel_id=(
                    select(SlackChannel.id)
                    # no index, but should be fine due to low table size
                    .where(SlackChannel.slack_id == SlackMessage.slack_channel_slack_id)
                    .limit(1)
                    .scalar_subquery()
                )
            )
        )
        session.exec(stmt)
        session.commit()

        # just want some logs for now. not going to retrofit everything in this file for logging
        logger.info("backfill_slack_messages_slack_channel_id complete")


def backfill_slack_messages_slack_team_id():
    with SessionManager() as session:
        stmt = (
            update(SlackMessage)
            .where(column("slack_team_id").is_(null()))
            .values(
                slack_team_id=(
                    select(SlackTeam.id)
                    # no index, but should be fine due to low table size
                    .where(SlackTeam.slack_id == SlackMessage.slack_team_slack_id)
                    .limit(1)
                    .scalar_subquery()
                )
            )
        )
        session.exec(stmt)
        session.commit()

        # just want some logs for now. not going to retrofit everything in this file for logging
        logger.info("backfill_slack_messages_slack_team_id complete")


def insert_genai_text(
    genai_text: GenAITextCreate,
    session: Optional[Session] = None,
) -> GenAIText:
    with SessionManager(session) as session:
        # db_genai_text = GenAIText.model_validate(genai_text)
        db_genai_text = genai_text.to_genai_text()
        session.add(db_genai_text)
        session.commit()
        session.refresh(db_genai_text)
        return db_genai_text


def get_genai_texts(
    session: Optional[Session] = None, skip: int = 0, limit: int = 100
) -> list[GenAIText]:
    with SessionManager(session) as session:
        stmt = select(GenAIText).offset(skip).limit(limit)
        return list(session.exec(stmt).all())


def get_genai_texts_by_slack_channel(
    slack_channel_slack_id: str, limit: int = 10, session: Optional[Session] = None
) -> list[GenAIText]:
    with SessionManager(session) as session:
        stmt = (
            select(GenAIText)
            .where(GenAIText.slack_channel_slack_id == slack_channel_slack_id)
            .order_by(GenAIText.created_at.desc())
            .limit(limit)
        )
        return list(session.exec(stmt).all())


def get_genai_text_by_id(
    genai_text_id: int, session: Optional[Session] = None
) -> GenAIText | None:
    with SessionManager(session) as session:
        stmt = select(GenAIText).where(GenAIText.id == genai_text_id)
        return session.exec(stmt).one_or_none()


def update_genai_text_response(
    genai_text_id: int,
    response: str,
    response_as_of: datetime.datetime = None,
    session: Optional[Session] = None,
) -> GenAIText | None:
    # TODO - this is ai generated. should this also take in or have the option to take in the genAI object?
    with SessionManager(session) as session:
        genai_text = session.get(GenAIText, genai_text_id)
        if genai_text:
            genai_text.response = response
            genai_text.response_as_of = response_as_of or datetime.datetime.now()
            session.add(genai_text)
            session.commit()
            session.refresh(genai_text)
        return genai_text


def backfill_genai_text_slack_channel_id(session: Optional[Session] = None):
    """
    Backfills the `slack_channel_id` for existing GenAIText entries based on
    the `slack_channel_slack_id` and the SlackChannel table.
    """
    with SessionManager(session) as session:
        stmt = (
            update(GenAIText)
            .where(
                column("slack_channel_id").is_(null())
            )  # Correctly references the column
            .values(
                slack_channel_id=(
                    select(SlackChannel.id)
                    .where(SlackChannel.slack_id == GenAIText.slack_channel_slack_id)
                    .limit(1)
                    .scalar_subquery()
                )
            )
        )
        session.exec(stmt)
        session.commit()
        logger.info("backfill_genai_text_slack_channel_id complete")


def backfill_genai_text_slack_user_id(session: Optional[Session] = None):
    """
    Backfills the `slack_user_id` for existing GenAIText entries based on
    the `slack_user_slack_id` and the SlackUser table.
    """
    with SessionManager(session) as session:
        stmt = (
            update(GenAIText)
            .where(
                column("slack_user_id").is_(null())
            )  # Correctly references the column
            .values(
                slack_user_id=(
                    select(SlackUser.id)
                    .where(SlackUser.slack_id == GenAIText.slack_user_slack_id)
                    .limit(1)
                    .scalar_subquery()
                )
            )
        )
        session.exec(stmt)
        session.commit()
        logger.info("backfill_genai_text_slack_user_id complete")


def insert_music_poll(
    music_poll: MusicPollCreate, session: Optional[Session] = None
) -> MusicPoll:
    with SessionManager(session) as session:
        db_music_poll = music_poll.to_music_poll()
        session.add(db_music_poll)
        session.commit()
        session.refresh(db_music_poll)
        return db_music_poll


def get_music_poll_by_id(
    music_poll_id: int, session: Optional[Session] = None
) -> MusicPoll | None:
    with SessionManager(session) as session:
        return session.get(MusicPoll, music_poll_id)


def get_music_polls(
    session: Optional[Session] = None, skip: int = 0, limit: int = 100
) -> list[MusicPoll]:
    with SessionManager(session) as session:
        stmt = select(MusicPoll).offset(skip).limit(limit)
        return list(session.exec(stmt).all())


def update_music_poll(
    music_poll_id: int, updates: dict[str, any], session: Optional[Session] = None
) -> MusicPoll | None:
    with SessionManager(session) as session:
        music_poll = db_update(session, MusicPoll, music_poll_id, updates)
    return music_poll


def delete_music_poll(music_poll_id: int, session: Optional[Session] = None) -> bool:
    with SessionManager(session) as session:
        music_poll = session.get(MusicPoll, music_poll_id)
        if music_poll:
            session.delete(music_poll)
            session.commit()
            return True
        return False


def insert_music_poll_instance(
    instance: MusicPollInstanceCreate, session: Optional[Session] = None
) -> MusicPollInstance:
    with SessionManager(session) as session:
        db_instance = instance.to_music_poll_instance()
        session.add(db_instance)
        session.commit()
        session.refresh(db_instance)
        return db_instance


def get_music_poll_instance_by_id(
    instance_id: int, session: Optional[Session] = None
) -> MusicPollInstance | None:
    with SessionManager(session) as session:
        return session.get(MusicPollInstance, instance_id)


def get_music_poll_instances(
    music_poll_id: int, session: Optional[Session] = None
) -> list[MusicPollInstance]:
    with SessionManager(session) as session:
        stmt = select(MusicPollInstance).where(
            MusicPollInstance.music_poll_id == music_poll_id
        )
        return list(session.exec(stmt).all())


def update_music_poll_instance(
    instance_id: int, updates: dict, session: Optional[Session] = None
) -> MusicPollInstance | None:
    with SessionManager(session) as session:
        instance = db_update(session, MusicPollInstance, instance_id, updates)
    return instance


def delete_music_poll_instance(
    instance_id: int, session: Optional[Session] = None
) -> bool:
    with SessionManager(session) as session:
        instance = session.get(MusicPollInstance, instance_id)
        if instance:
            session.delete(instance)
            session.commit()
            return True
        return False


def insert_music_poll_response(
    response: MusicPollResponseCreate, session: Optional[Session] = None
) -> MusicPollResponse:
    with SessionManager(session) as session:
        db_response = response.to_music_poll_response()
        session.add(db_response)
        session.commit()
        session.refresh(db_response)
        return db_response


def get_music_poll_response_by_id(
    response_id: int, session: Optional[Session] = None
) -> MusicPollResponse | None:
    with SessionManager(session) as session:
        return session.get(MusicPollResponse, response_id)


def get_music_poll_responses(
    instance_id: int, session: Optional[Session] = None
) -> list[MusicPollResponse]:
    with SessionManager(session) as session:
        stmt = select(MusicPollResponse).where(
            MusicPollResponse.music_poll_instance_id == instance_id
        )
        return list(session.exec(stmt).all())


def update_music_poll_response(
    response_id: int, updates: dict, session: Optional[Session] = None
) -> MusicPollResponse | None:
    with SessionManager(session) as session:
        response = db_update(session, MusicPollResponse, response_id, updates)
    return response


def delete_music_poll_response(
    response_id: int, session: Optional[Session] = None
) -> bool:
    with SessionManager(session) as session:
        response = session.get(MusicPollResponse, response_id)
        if response:
            session.delete(response)
            session.commit()
            return True
        return False
