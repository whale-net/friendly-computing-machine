import enum
from datetime import datetime

from sqlalchemy import func
from sqlmodel import Field
from friendly_computing_machine.models.base import Base


# -----
# Task
class TaskBase(Base):
    name: str = Field(unique=True)


class Task(TaskBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class TaskCreate(TaskBase):
    pass


# -----
# TaskInstance
class TaskInstanceStatus(enum.Enum):
    UNKNOWN = 0
    OK = 1
    FAIL = 2
    SKIPPED = 3
    EXCEPTION = 4


class TaskInstanceBase(Base):
    task_id: int = Field(foreign_key="task.id")
    # one date, not planning on updating the database that often
    as_of: datetime = Field(default_factory=func.now)
    status: TaskInstanceStatus


class TaskInstance(TaskInstanceBase, table=True):
    id: int = Field(default=None, nullable=False, primary_key=True)


class TaskInstanceCreate(TaskInstanceBase):
    def to_task_instance(self) -> TaskInstance:
        # there has to be a more intelligent way to do this
        return TaskInstance(
            task_id=self.task_id,
            as_of=self.as_of,
            status=self.status,
        )


# TODO - taskpool instance
