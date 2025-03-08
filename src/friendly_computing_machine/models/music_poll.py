import datetime

from sqlmodel import Field
from sqlalchemy import func, Column, DateTime

from friendly_computing_machine.models.base import Base


class MusicPollBase(Base):
    slack_channel_id: int = Field(foreign_key="slackchannel.id", index=True)
    start_date: datetime.datetime = Field()
    name: str = Field()


class MusicPoll(MusicPollBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class MusicPollCreate(MusicPollBase):
    def to_music_poll(self) -> MusicPoll:
        return MusicPoll(
            slack_channel_id=self.slack_channel_id,
            start_date=self.start_date,
            name=self.name,
        )


class MusicPollInstanceBase(Base):
    music_poll_id: int = Field(foreign_key="musicpoll.id", index=True)
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
        ),
    )
    closed_at: datetime.datetime = Field(nullable=True)


class MusicPollInstance(MusicPollInstanceBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class MusicPollInstanceCreate(MusicPollInstanceBase):
    def to_music_poll_instance(self) -> MusicPollInstance:
        return MusicPollInstance(
            music_poll_id=self.music_poll_id,
            created_at=self.created_at,
            closed_at=self.closed_at,
        )


class MusicPollResponseBase(Base):
    music_poll_instance_id: int = Field(foreign_key="musicpollinstance.id", index=True)
    slack_user_id: int = Field(foreign_key="slackuser.id", index=True)
    slack_message_id: int = Field(foreign_key="slackmessage.id", index=True)
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
        ),
    )
    # for now, going to store URL here
    # in future, may want to store more metadata in a separate table
    url: str = Field()


class MusicPollResponse(MusicPollResponseBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class MusicPollResponseCreate(MusicPollResponseBase):
    def to_music_poll_response(self) -> MusicPollResponse:
        return MusicPollResponse(
            music_poll_instance_id=self.music_poll_instance_id,
            slack_user_id=self.slack_user_id,
            slack_message_id=self.slack_message_id,
            created_at=self.created_at,
            url=self.url,
        )
