import logging
import os

from typing import Annotated
import typer


# TODO what is ... doing? can I name it?
T_slack_app_token = Annotated[str, typer.Option(..., envvar="SLACK_APP_TOKEN")]
FILENAME = os.path.basename(__file__)
logger = logging.getLogger(__name__)


def setup_slack(
    ctx: typer.Context,
    slack_app_token: T_slack_app_token,
):
    logger.debug("slack setup starting")
    ctx.obj[FILENAME] = {
        "slack_app_token": slack_app_token,
    }
    logger.debug("slack setup complete")
