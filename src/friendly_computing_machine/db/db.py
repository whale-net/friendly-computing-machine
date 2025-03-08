import logging
from typing import Optional

import alembic
import alembic.command
import alembic.config
from sqlalchemy import Engine
from sqlmodel import Session, create_engine

__GLOBALS = {"engine": None}


logger = logging.getLogger(__name__)


def init_engine(url: str, echo: bool = False):
    if __GLOBALS["engine"] is not None:
        raise RuntimeError("double engine init")
    __GLOBALS["engine"] = create_engine(
        url, echo=echo, pool_pre_ping=True, pool_recycle=60
    )
    logger.info("engine created")


def get_engine() -> Engine:
    if __GLOBALS["engine"] is None:
        raise RuntimeError("engine is none")
    return __GLOBALS["engine"]


class SessionManager:
    def __init__(self, session: Optional[Session] = None):
        # TODO autocommit
        # TODO rollback on error
        # TODO transaction? this suggestion came from AI
        # close the session if it was made by this instance
        self.should_close = session is None
        # session is established during init instead of enter.
        # shouldn't be problematic, but maybe in some odd situation
        self.session = session or Session(get_engine())

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback):
        # unexpected to get here
        if self.session is None:
            raise RuntimeError("session is none, exit called without init")
        if self.should_close:
            self.session.close()
        else:
            logger.debug("session is passthrough, not closing")


def run_migration(config: alembic.config.Config):
    with get_engine().begin() as connection:
        config.attributes["connection"] = connection
        alembic.command.upgrade(config, "head")


def should_run_migration(config: alembic.config.Config) -> bool:
    with get_engine().begin() as conn:
        config.attributes["connection"] = conn
        try:
            alembic.command.check(config)
        except alembic.command.util.AutogenerateDiffsDetected:
            return True

        return False


def create_migration(config: alembic.config.Config, message: Optional[str]):
    if not should_run_migration(config):
        logger.info("no migration required")
        raise RuntimeError("no migration required")
    with get_engine().begin() as conn:
        config.attributes["connection"] = conn
        alembic.command.revision(config, message=message, autogenerate=True)


def run_downgrade(config: alembic.config.Config, revision: str):
    with get_engine().begin() as connection:
        config.attributes["connection"] = connection
        alembic.command.downgrade(config, revision)
