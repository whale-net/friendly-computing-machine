import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field

from friendly_computing_machine.models.base import Base


class PollBase(Base):
    title: str = Field()
    description: Optional[str] = Field(default=None)
    slack_channel_slack_id: str = Field(index=True)
    slack_user_slack_id: str = Field(index=True)  # creator of the poll
    slack_message_id: Optional[int] = Field(default=None, foreign_key="slackmessage.id")
    slack_message_ts: Optional[str] = Field(default=None)  # for message updates
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
        ),
    )
    expires_at: datetime.datetime = Field()
    is_active: bool = Field(default=True)


class Poll(PollBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class PollCreate(PollBase):
    def to_poll(self) -> Poll:
        return Poll(
            title=self.title,
            description=self.description,
            slack_channel_slack_id=self.slack_channel_slack_id,
            slack_user_slack_id=self.slack_user_slack_id,
            slack_message_id=self.slack_message_id,
            slack_message_ts=self.slack_message_ts,
            created_at=self.created_at,
            expires_at=self.expires_at,
            is_active=self.is_active,
        )


class PollOptionBase(Base):
    poll_id: int = Field(foreign_key="poll.id", index=True)
    text: str = Field()
    display_order: int = Field(default=0)


class PollOption(PollOptionBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class PollOptionCreate(PollOptionBase):
    def to_poll_option(self) -> PollOption:
        return PollOption(
            poll_id=self.poll_id,
            text=self.text,
            display_order=self.display_order,
        )


class PollVoteBase(Base):
    poll_id: int = Field(foreign_key="poll.id", index=True)
    poll_option_id: int = Field(foreign_key="polloption.id", index=True)
    slack_user_slack_id: str = Field(index=True)
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
        ),
    )


class PollVote(PollVoteBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class PollVoteCreate(PollVoteBase):
    def to_poll_vote(self) -> PollVote:
        return PollVote(
            poll_id=self.poll_id,
            poll_option_id=self.poll_option_id,
            slack_user_slack_id=self.slack_user_slack_id,
            created_at=self.created_at,
        )