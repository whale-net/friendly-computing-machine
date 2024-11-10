import typer
from typing import Annotated, Optional

import alembic.config

from friendly_computing_machine.bot import (
    run_slack_bot,
    slack_bot_who_am_i,
    slack_send_message,
)
from friendly_computing_machine.db import (
    init_engine,
    run_migration,
    create_migration,
    should_run_migration,
)

# TODO - multi app - need to check multi app callback logic
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


# @app.command("migrations-test")
# TODO - merge?


@app.command("bot-run")
def cli_run(skip_migration_check: bool = False):
    if not skip_migration_check and should_run_migration(cli_context["alembic_config"]):
        raise RuntimeError("need to run migration")
    run_slack_bot(
        app_token=cli_context["SLACK_APP_TOKEN"]
    )  # , bot_token=cli_context["SLACK_BOT_TOKEN"])


@app.command("bot-send-test-command")
def cli_bot_test_message(channel: str, message: str):
    slack_send_message(channel, message)


@app.command("bot-who-am-i")
def cli_bot_who_am_i():
    slack_bot_who_am_i()


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
