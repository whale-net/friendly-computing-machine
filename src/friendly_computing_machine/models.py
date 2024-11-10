from sqlmodel import SQLModel, Field, MetaData


class Base(SQLModel):
    # set schema. not required because isolating apps+environments via database
    # but may as well specify to avoid ambiguity
    metadata = MetaData(schema="fcm")


# Trying out a different way to build these models, copied from a tutorial that seems to have a better grasp on this
# than I did when working on manman
# So, rather than having one model for everything, going to create multiple classes that work together
# unsure of benefits or drawbacks as of writing
class SlackTeamBase(Base):
    slack_id: str
    name: str


class SlackTeam(SlackTeamBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


# read-only pydantic? unsure how it's used
class SlackTeamCreate(SlackTeamBase):
    pass
