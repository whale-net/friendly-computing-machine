import logging
import os
from typing import Annotated

import alembic.config
import typer

from friendly_computing_machine.bot.cli import app as bot_app
from friendly_computing_machine.cli.tools import app as tool_app
from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.cli import migration_app
from friendly_computing_machine.db.db import init_engine


from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import ConsoleLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

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
    google_api_key: Annotated[str, typer.Option(envvar="GOOGLE_API_KEY")],
    debug: bool = False,
    log_otlp: bool = True,
    log_console: bool = False,
):
    # OTEL logging setup
    logger_provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": "friendly-computing-machine",
                "service.instance.id": os.uname().nodename,
            }
        ),
    )
    set_logger_provider(logger_provider)

    if log_otlp:
        otlp_exporter = OTLPLogExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT")
            or "http://0.0.0.0:4317",
            insecure=True,
        )
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    if log_console:
        console_exporter = ConsoleLogExporter()
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(console_exporter)
        )

    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    logging.getLogger().addHandler(handler)

    logger.debug("CLI callback starting")

    CliContext(
        slack_app_token,
        # TODO: this default may prove problematic with containerization
        # TODO - is this overwritten or ignored? I think it may be but idc enough to test
        alembic.config.Config("./alembic.ini"),
        google_api_key,
    )
    # print(context)

    init_engine(database_url)

    logger.debug("CLI callback complete")
