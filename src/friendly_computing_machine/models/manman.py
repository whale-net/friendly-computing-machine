import datetime

from sqlmodel import Field

from external.manman_status_api.models.status_info import StatusInfo
from friendly_computing_machine.models.base import Base


class ManManStatusUpdateBase(Base):
    """
    Represents a status update for ManMan.
    """

    current_status: str
    # "server" or "worker"
    service_type: str
    # the primary key id
    # could be string for future proof but we'll get there when we get there
    service_id: int

    as_of: datetime.datetime


class ManManStatusUpdate(ManManStatusUpdateBase, table=True):
    """
    Represents a status update for ManMan, stored in the database.
    """

    id: int = Field(default=None, nullable=False, primary_key=True)


class ManManStatusUpdateCreate(ManManStatusUpdateBase):
    @classmethod
    def from_status_info(cls, status_info: StatusInfo) -> "ManManStatusUpdateCreate":
        """
        Create a ManManStatusUpdateCreate instance from a StatusInfo instance.
        """

        service_type = (
            "server" if status_info.game_server_instance_id is not None else "worker"
        )
        service_id = status_info.game_server_instance_id or status_info.worker_id

        return cls(
            current_status=status_info.status_type.value,
            service_type=service_type,
            service_id=service_id,
            as_of=status_info.as_of,
        )
