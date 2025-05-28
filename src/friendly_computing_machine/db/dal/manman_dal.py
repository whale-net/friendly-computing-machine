"""ManMan model DAL functions."""

import logging
from typing import Optional

from sqlmodel import Session, select

from friendly_computing_machine.db.util import SessionManager, db_update
from friendly_computing_machine.models.manman import (
    ManManStatusUpdate,
    ManManStatusUpdateCreate,
)

logger = logging.getLogger(__name__)


def insert_manman_status_update(
    manman_status_update: ManManStatusUpdateCreate, session: Optional[Session] = None
) -> ManManStatusUpdate:
    """Insert a new ManMan status update."""
    with SessionManager(session) as session:
        db_manman_status_update = ManManStatusUpdate.model_validate(
            manman_status_update
        )
        session.add(db_manman_status_update)
        session.commit()
        session.refresh(db_manman_status_update)
        return db_manman_status_update


def get_manman_status_update_by_id(
    manman_status_update_id: int, session: Optional[Session] = None
) -> ManManStatusUpdate | None:
    """Get a ManMan status update by ID."""
    with SessionManager(session) as session:
        return session.get(ManManStatusUpdate, manman_status_update_id)


def get_manman_status_update_from_create(
    manman_status_update_create: ManManStatusUpdateCreate,
    session: Optional[Session] = None,
) -> ManManStatusUpdate:
    """Get a ManMan status update from a ManManStatusUpdateCreate instance."""
    with SessionManager(session) as session:
        stmt = select(ManManStatusUpdate).where(
            ManManStatusUpdate.service_type == manman_status_update_create.service_type,
            ManManStatusUpdate.service_id == manman_status_update_create.service_id,
        )
        code = session.exec(stmt).first()
        if not code:
            raise ValueError(
                f"No ManManStatusUpdate found for service_type={manman_status_update_create.service_type} "
                f"and service_id={manman_status_update_create.service_id}"
            )
        logger.info("found ManManStatusUpdate.id=%s", code.id)
        return code


def get_manman_status_updates(
    session: Optional[Session] = None, skip: int = 0, limit: int = 100
) -> list[ManManStatusUpdate]:
    """Get ManMan status updates with pagination."""
    with SessionManager(session) as session:
        stmt = select(ManManStatusUpdate).offset(skip).limit(limit)
        return list(session.exec(stmt).all())


def update_manman_status_update(
    manman_status_update_id: int,
    updates: dict[str, any],
    session: Optional[Session] = None,
) -> ManManStatusUpdate | None:
    """Update a ManMan status update."""
    with SessionManager(session) as session:
        manman_status_update = db_update(
            session, ManManStatusUpdate, manman_status_update_id, updates
        )
    return manman_status_update


def delete_manman_status_update(
    manman_status_update_id: int, session: Optional[Session] = None
) -> bool:
    """Delete a ManMan status update."""
    with SessionManager(session) as session:
        manman_status_update = session.get(ManManStatusUpdate, manman_status_update_id)
        if manman_status_update:
            session.delete(manman_status_update)
            session.commit()
            return True
        return False
