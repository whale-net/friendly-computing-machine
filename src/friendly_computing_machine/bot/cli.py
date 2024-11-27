import typer

from friendly_computing_machine.bot.bot import (
    run_slack_bot,
    slack_bot_who_am_i,
    slack_send_message,
)
from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.db import (
    should_run_migration,
)


app = typer.Typer()


@app.command("run")
def cli_run(skip_migration_check: bool = False):
    context = CliContext.get_instance()
    if skip_migration_check:
        print("skipping migration, starting normally")
    elif should_run_migration(context.alembic_config):
        raise RuntimeError("need to run migration")
    else:
        print("no migration, starting normally")
    run_slack_bot(app_token=context.slack_app_token)


@app.command("send-test-command")
def cli_bot_test_message(channel: str, message: str):
    slack_send_message(channel, message)


@app.command("who-am-i")
def cli_bot_who_am_i():
    slack_bot_who_am_i()
