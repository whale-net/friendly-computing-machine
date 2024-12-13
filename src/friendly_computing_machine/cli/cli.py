import logging
from typing import Annotated

import alembic.config
import typer

from friendly_computing_machine.bot.cli import app as bot_app
from friendly_computing_machine.cli.tools import app as tool_app
from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.cli import migration_app
from friendly_computing_machine.db.db import init_engine

logger = logging.getLogger(__name__)

# TODO - multi app - need to check multi app callback logic
app = typer.Typer()
app.add_typer(bot_app, name="bot")
app.add_typer(migration_app, name="migration")
app.add_typer(tool_app, name="tools")


@bot_app.callback()
@migration_app.callback()
def callback(
    slack_app_token: Annotated[str, typer.Option(envvar="SLACK_APP_TOKEN")],
    # slack_bot_token: Annotated[str, typer.Option(envvar="SLACK_BOT_TOKEN")],
    database_url: Annotated[str, typer.Option(envvar="DATABASE_URL")],
    debug: bool = False,
):
    CliContext(
        slack_app_token,
        # TODO: this default may prove problematic with containerization
        # TODO - is this overwritten or ignored? I think it may be but idc enough to test
        alembic.config.Config("./alembic.ini"),
    )
    # print(context)

    init_engine(database_url)

    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level)
    logger.info("CLI callback complete")
