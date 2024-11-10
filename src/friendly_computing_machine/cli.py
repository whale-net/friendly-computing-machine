import typer
from typing import Annotated, Optional

import alembic.config

from friendly_computing_machine.bot import run_slack_bot
from friendly_computing_machine.db import (
    init_engine,
    run_migration,
    create_migration,
    should_run_migration,
)

app = typer.Typer()

cli_context = {
    "SLACK_APP_TOKEN": "",
    # "SLACK_BOT_TOKEN": "",
    "alembic_config": None,
}


@app.command("migrations-run")
def cli_migration_run():
    run_migration(cli_context["alembic_config"])


@app.command("migrations-create")
def cli_migration_create(message: Optional[str] = None):
    create_migration(cli_context["alembic_config"], message)


@app.command("bot-run")
def cli_run(skip_migration_check: bool = False):
    if not skip_migration_check and should_run_migration(cli_context["alembic_config"]):
        raise RuntimeError("need to run migration")
    run_slack_bot(
        app_token=cli_context["SLACK_APP_TOKEN"]
    )  # , bot_token=cli_context["SLACK_BOT_TOKEN"])


@app.callback()
def callback(
    slack_app_token: Annotated[str, typer.Option(envvar="SLACK_APP_TOKEN")],
    # slack_bot_token: Annotated[str, typer.Option(envvar="SLACK_BOT_TOKEN")],
    database_url: Annotated[str, typer.Option(envvar="DATABASE_URL")],
):
    cli_context["SLACK_APP_TOKEN"] = slack_app_token
    # cli_context["SLACK_BOT_TOKEN"] = slack_bot_token

    # TODO: this default may prove problematic with containerization
    cli_context["alembic_config"] = alembic.config.Config("./alembic.ini")
    init_engine(database_url)
