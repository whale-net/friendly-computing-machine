import typer
from typing import Optional

from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.db import (
    run_migration,
    create_migration,
)


migration_app = typer.Typer()

@migration_app.command("run")
def cli_migration_run():
    context = CliContext.get_instance()
    run_migration(context.alembic_config)


@migration_app.command("create")
def cli_migration_create(message: Optional[str] = None):
    context = CliContext.get_instance()
    create_migration(context.alembic_config, message)
