import datetime
from typing import Optional

from sqlmodel import Field

from friendly_computing_machine.models.base import Base


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
    pass


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
