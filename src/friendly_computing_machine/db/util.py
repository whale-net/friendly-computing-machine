import logging

from sqlmodel import Session

from friendly_computing_machine.models.base import Base

logger = logging.getLogger(__name__)


def validate_model_fields(model_class: Base, updates: dict) -> tuple[dict, dict]:
    """Validate and filter update fields against a model's fields.

    Args:
        model_class: The SQLModel class to validate against
        updates: Dictionary of field updates to validate

    Returns:
        Tuple of (valid_updates, invalid_updates) where each is a dictionary.
        valid_updates contains fields that exist in the model
        invalid_updates contains fields that don't exist in the model
    """
    valid_fields = model_class.model_fields.keys()
    valid_updates = {k: v for k, v in updates.items() if k in valid_fields}
    invalid_updates = {k: v for k, v in updates.items() if k not in valid_fields}

    if len(invalid_updates) > 0:
        logger.warning(
            "Invalid updates for %s: %s",
            model_class.__name__,
            invalid_updates,
        )

    return valid_updates, invalid_updates


def validate_model_fields_list(
    model_class: Base, updates: list[dict]
) -> list[tuple[dict, dict]]:
    """Validate and filter update fields against a model's fields.

    Args:
        model_class: The SQLModel class to validate against
        updates: List of dictionaries of field updates to validate
    Returns:
        List of dictionaries with valid updates
    """
    # do if needed
    raise NotImplementedError("validate_model_fields_list is not implemented yet")


def db_update(
    session: Session, model_class: Base, model_id: int, updates: dict
) -> Base | None:
    """Update a model instance in the database.

    Args:
        session: SQLAlchemy session
        model_class: The SQLModel class to update
        updates: Dictionary of field updates

    Returns:
        Updated model instance
    """
    valid_updates, _ = validate_model_fields(model_class, updates)
    if len(valid_updates) == 0:
        logger.info("No valid updates for %s", model_class.__name__)
        return None

    instance = session.get(model_class, model_id)

    if not instance:
        logger.info(
            "Instance not found for %s with id=%s", model_class.__name__, model_id
        )
        return None

    for key, value in valid_updates.items():
        setattr(instance, key, value)

    session.commit()
    session.refresh(instance)
    return instance
