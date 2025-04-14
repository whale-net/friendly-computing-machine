import logging
from typing import Annotated

import alembic.config
import typer

from friendly_computing_machine.cli.bot_cli import app as bot_app
from friendly_computing_machine.cli.tools_cli import app as tool_app
from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.cli.migration_cli import migration_app
from friendly_computing_machine.db.db import init_engine

from friendly_computing_machine.cli.context.log import setup_logging


logger = logging.getLogger(__name__)

app = typer.Typer()
app.add_typer(bot_app, name="bot")
app.add_typer(migration_app, name="migration")
app.add_typer(tool_app, name="tools")


@bot_app.callback()
@migration_app.callback()
def callback(
    ctx: typer.Context,
    # slack_bot_token: Annotated[str, typer.Option(envvar="SLACK_BOT_TOKEN")],
    database_url: Annotated[str, typer.Option(envvar="DATABASE_URL")],
):
    logger.debug("CLI callback starting")

    setup_logging(ctx)

    CliContext(
        "",
        # TODO: this default may prove problematic with containerization
        # TODO - is this overwritten or ignored? I think it may be but idc enough to test
        alembic.config.Config("./alembic.ini"),
        "",
    )

    # print(context)

    init_engine(database_url)

    logger.debug("CLI callback complete")
