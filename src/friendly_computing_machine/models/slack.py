import datetime
from typing import Optional, Any, Dict

from sqlmodel import Field

from friendly_computing_machine.models.base import Base
from friendly_computing_machine.util import ts_to_datetime


# -----
# team
class SlackTeamBase(Base):
    slack_id: str = Field(index=True, unique=True)
    name: str


class SlackTeam(SlackTeamBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


# read-only pydantic? unsure of the benefit of this
# I think it's so that any extra creation info can be contained in this class rather in the base class
# going to try it out
class SlackTeamCreate(SlackTeamBase):
    def to_slack_team(self) -> SlackTeam:
        return SlackTeam(
            slack_id=self.slack_id,
            name=self.name,
        )


# -----
# user
class SlackUserBase(Base):
    slack_id: str = Field(index=True, unique=True)
    name: str
    is_bot: bool = False
    slack_team_slack_id: str = Field(nullable=True)


class SlackUser(SlackUserBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)
    slack_team_id: int = Field(nullable=True, foreign_key="slackteam.id", index=True)


class SlackUserCreate(SlackUserBase):
    def to_slack_user(self, slack_team_id: Optional[int] = None) -> SlackUser:
        # TBD if slack_team_id should be non-optional
        return SlackUser(
            slack_id=self.slack_id,
            name=self.name,
            is_bot=self.is_bot,
            slack_team_slack_id=self.slack_team_slack_id,
            slack_team_id=slack_team_id,
        )


# -----
# message
class SlackMessageBase(Base):
    slack_id: str | None = Field(index=True)
    slack_team_slack_id: str
    slack_channel_slack_id: str
    slack_user_slack_id: str
    text: str
    ts: datetime.datetime
    # if not null, is thread
    thread_ts: datetime.datetime | None
    # unsure how to make sense of this since I am testing with only one user - but seems useful
    parent_user_slack_id: str | None


class SlackMessage(SlackMessageBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)
    # time that this message was processed and updated
    processed_date: datetime.datetime | None
    slack_team_id: int = Field(nullable=True, foreign_key="slackteam.id", index=True)
    slack_channel_id: int = Field(
        nullable=True, foreign_key="slackchannel.id", index=True
    )
    slack_user_id: int = Field(nullable=True, foreign_key="slackuser.id", index=True)
    slack_parent_user_id: int = Field(
        nullable=True, foreign_key="slackuser.id", index=True
    )


class SlackMessageCreate(SlackMessageBase):
    @classmethod
    def from_slack_message_json(
        cls, message_event: Dict[str, Any]
    ) -> "SlackMessageCreate":
        thread_ts = message_event.get("thread_ts")
        message = SlackMessageCreate(
            slack_id=message_event.get("client_msg_id"),
            slack_team_slack_id=message_event.get("team"),
            slack_channel_slack_id=message_event.get("channel"),  #
            slack_user_slack_id=message_event.get("user"),
            text=message_event.get("text"),
            ts=ts_to_datetime(message_event.get("ts")),
            thread_ts=ts_to_datetime(thread_ts) if thread_ts else None,
            parent_user_slack_id=message_event.get("parent_user_id"),
        )
        return message


# -----
# channel
class SlackChannelBase(Base):
    slack_id: str = Field(index=True, unique=True)
    name: str
    channel_type: str
    # TODO deprecated
    is_music_poll: bool = Field(default=False)


class SlackChannel(SlackChannelBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class SlackChannelCreate(SlackChannelBase):
    pass
