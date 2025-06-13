import logging
from typing import List, Optional

from sqlmodel import Session, select

from friendly_computing_machine.db.util import get_db_connection
from friendly_computing_machine.models.poll import (
    Poll,
    PollCreate,
    PollOption,
    PollOptionCreate,
    PollVote,
    PollVoteCreate,
)

logger = logging.getLogger(__name__)


def insert_poll(poll_create: PollCreate) -> Poll:
    """Insert a new poll into the database."""
    with Session(get_db_connection()) as session:
        poll = poll_create.to_poll()
        session.add(poll)
        session.commit()
        session.refresh(poll)
        return poll


def get_poll_by_id(poll_id: int) -> Optional[Poll]:
    """Get a poll by its ID."""
    with Session(get_db_connection()) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        return session.exec(statement).first()


def update_poll_message_info(
    poll_id: int, slack_message_id: int, slack_message_ts: str
) -> Poll:
    """Update poll with Slack message information."""
    with Session(get_db_connection()) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        poll = session.exec(statement).first()
        if not poll:
            raise ValueError(f"Poll with id {poll_id} not found")

        poll.slack_message_id = slack_message_id
        poll.slack_message_ts = slack_message_ts
        session.add(poll)
        session.commit()
        session.refresh(poll)
        return poll


def update_poll_workflow_id(poll_id: int, workflow_id: str) -> Poll:
    """Update poll with temporal workflow ID."""
    with Session(get_db_connection()) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        poll = session.exec(statement).first()
        if not poll:
            raise ValueError(f"Poll with id {poll_id} not found")

        poll.workflow_id = workflow_id
        session.add(poll)
        session.commit()
        session.refresh(poll)
        return poll


def deactivate_poll(poll_id: int) -> Poll:
    """Deactivate a poll."""
    with Session(get_db_connection()) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        poll = session.exec(statement).first()
        if not poll:
            raise ValueError(f"Poll with id {poll_id} not found")

        poll.is_active = False
        session.add(poll)
        session.commit()
        session.refresh(poll)
        return poll


def insert_poll_options(poll_options: List[PollOptionCreate]) -> List[PollOption]:
    """Insert multiple poll options."""
    with Session(get_db_connection()) as session:
        options = [option_create.to_poll_option() for option_create in poll_options]
        session.add_all(options)
        session.commit()
        for option in options:
            session.refresh(option)
        return options


def get_poll_options(poll_id: int) -> List[PollOption]:
    """Get all options for a poll, ordered by display_order."""
    with Session(get_db_connection()) as session:
        statement = (
            select(PollOption)
            .where(PollOption.poll_id == poll_id)
            .order_by(PollOption.display_order)
        )
        return list(session.exec(statement).all())


def insert_poll_vote(vote_create: PollVoteCreate) -> PollVote:
    """Insert a new poll vote."""
    with Session(get_db_connection()) as session:
        # Check if user already voted for this poll
        existing_vote_statement = select(PollVote).where(
            PollVote.poll_id == vote_create.poll_id,
            PollVote.slack_user_slack_id == vote_create.slack_user_slack_id,
        )
        existing_vote = session.exec(existing_vote_statement).first()

        if existing_vote:
            # Update existing vote
            existing_vote.poll_option_id = vote_create.poll_option_id
            session.add(existing_vote)
            session.commit()
            session.refresh(existing_vote)
            return existing_vote
        else:
            # Create new vote
            vote = vote_create.to_poll_vote()
            session.add(vote)
            session.commit()
            session.refresh(vote)
            return vote


def get_poll_votes(poll_id: int) -> List[PollVote]:
    """Get all votes for a poll."""
    with Session(get_db_connection()) as session:
        statement = select(PollVote).where(PollVote.poll_id == poll_id)
        return list(session.exec(statement).all())


def get_poll_vote_counts(poll_id: int) -> dict:
    """Get vote counts per option for a poll."""
    votes = get_poll_votes(poll_id)
    vote_counts = {}
    for vote in votes:
        if vote.poll_option_id not in vote_counts:
            vote_counts[vote.poll_option_id] = 0
        vote_counts[vote.poll_option_id] += 1
    return vote_counts


def get_poll_voters_by_option(poll_id: int) -> dict:
    """Get voters grouped by option for a poll."""
    votes = get_poll_votes(poll_id)
    voters_by_option = {}
    for vote in votes:
        if vote.poll_option_id not in voters_by_option:
            voters_by_option[vote.poll_option_id] = []
        voters_by_option[vote.poll_option_id].append(vote.slack_user_slack_id)
    return voters_by_option
