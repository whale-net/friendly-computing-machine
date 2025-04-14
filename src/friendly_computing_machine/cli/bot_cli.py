import logging

import typer

from friendly_computing_machine.bot.main import run_slack_bot
from friendly_computing_machine.bot.util import slack_bot_who_am_i, slack_send_message
from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.db import should_run_migration

from friendly_computing_machine.cli.context.slack import setup_slack, T_slack_app_token
from friendly_computing_machine.cli.context.gemini import setup_gemini, T_google_api_key

logger = logging.getLogger(__name__)

app = typer.Typer(
    context_settings={"obj": {}},
)


@app.command("run")
def cli_run(
    ctx: typer.Context,
    slack_app_token: T_slack_app_token,
    google_api_key: T_google_api_key,
    skip_migration_check: bool = False,
):
    context = CliContext.get_instance()
    if skip_migration_check:
        logger.info("skipping migration check")
    elif should_run_migration(context.alembic_config):
        logger.critical("migration check failed, please migrate")
        raise RuntimeError("need to run migration")
    else:
        logger.info("migration check passed, starting normally")

    logger.info("genai setup")

    setup_gemini(ctx, google_api_key)
    # TODO put setup slack in callback
    setup_slack(ctx, slack_app_token)
    run_slack_bot(app_token=ctx.obj["slack_app_token"])


@app.command("send-test-command")
def cli_bot_test_message(channel: str, message: str):
    slack_send_message(channel, message)


@app.command("who-am-i")
def cli_bot_who_am_i():
    slack_bot_who_am_i()
