import datetime

from sqlmodel import Field
from sqlalchemy import func, Column, DateTime

from friendly_computing_machine.models.base import Base


class GenAITextBase(Base):
    slack_channel_slack_id: str = Field(index=True)
    slack_user_slack_id: str = Field(index=True)
    prompt: str
    created_at: datetime.datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.current_timestamp(), index=True
        ),
    )
    response: str
    response_as_of: datetime.datetime = Field(index=True, nullable=True)


class GenAIText(GenAITextBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)
    slack_channel_id: int = Field(
        nullable=True, foreign_key="slackchannel.id", index=True
    )
    slack_user_id: int = Field(nullable=True, foreign_key="slackuser.id", index=True)


class GenAITextCreate(GenAITextBase):
    pass
