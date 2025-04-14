import logging

import typer

from friendly_computing_machine.bot.main import run_slack_bot
from friendly_computing_machine.bot.util import slack_bot_who_am_i, slack_send_message
from friendly_computing_machine.db.db import should_run_migration

from friendly_computing_machine.cli.context.slack import (
    setup_slack,
    T_slack_app_token,
    FILENAME as SLACK_FILENAME,
)
from friendly_computing_machine.cli.context.gemini import setup_gemini, T_google_api_key
from friendly_computing_machine.cli.context.db import (
    setup_db,
    T_database_url,
    FILENAME as DB_FILENAME,
)
from friendly_computing_machine.cli.context.log import setup_logging

logger = logging.getLogger(__name__)

app = typer.Typer(
    context_settings={"obj": {}},
)


@app.callback()
def callback(
    ctx: typer.Context,
    # slack_bot_token: Annotated[str, typer.Option(envvar="SLACK_BOT_TOKEN")],
    slack_app_token: T_slack_app_token,
):
    logger.debug("CLI callback starting")
    setup_logging(ctx)
    setup_slack(ctx, slack_app_token)
    logger.debug("CLI callback complete")


@app.command("run")
def cli_run(
    ctx: typer.Context,
    # keeping these on run for now just since it seems right
    google_api_key: T_google_api_key,
    database_url: T_database_url,
    skip_migration_check: bool = False,
):
    setup_db(ctx, database_url)
    if skip_migration_check:
        logger.info("skipping migration check")
    elif should_run_migration(
        ctx.obj[DB_FILENAME].engine, ctx.obj[DB_FILENAME].alembic_config
    ):
        logger.critical("migration check failed, please migrate")
        raise RuntimeError("need to run migration")
    else:
        logger.info("migration check passed, starting normally")

    setup_gemini(ctx, google_api_key)

    logger.info("starting bot")
    run_slack_bot(app_token=ctx.obj[SLACK_FILENAME]["slack_app_token"])


@app.command("send-test-command")
def cli_bot_test_message(channel: str, message: str):
    slack_send_message(channel, message)


@app.command("who-am-i")
def cli_bot_who_am_i():
    logger.info(slack_bot_who_am_i())
