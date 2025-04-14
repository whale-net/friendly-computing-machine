import logging

import typer

from friendly_computing_machine.cli.bot_cli import app as bot_app
from friendly_computing_machine.cli.tools_cli import app as tool_app
from friendly_computing_machine.cli.migration_cli import migration_app


logger = logging.getLogger(__name__)

app = typer.Typer()
app.add_typer(bot_app, name="bot")
app.add_typer(migration_app, name="migration")
app.add_typer(tool_app, name="tools")
