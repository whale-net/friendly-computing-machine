import logging
from typing import Optional

import typer

from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.db import create_migration, run_migration

logger = logging.getLogger(__name__)

migration_app = typer.Typer()


@migration_app.command("run")
def cli_migration_run():
    context = CliContext.get_instance()
    logger.info("running migration")
    run_migration(context.alembic_config)
    logger.info("migration complete")


@migration_app.command("create")
def cli_migration_create(message: Optional[str] = None):
    context = CliContext.get_instance()
    logger.info("creating migration")
    create_migration(context.alembic_config, message)
    logger.info("migration created")
