import logging
import os
from typing import Annotated

import typer

T_rabbitmq_url = Annotated[str, typer.Option(..., envvar="RABBITMQ_URL")]
FILENAME = os.path.basename(__file__)
logger = logging.getLogger(__name__)


def setup_rabbitmq(
    ctx: typer.Context,
    rabbitmq_url: T_rabbitmq_url,
):
    logger.debug("rabbitmq setup starting")
    ctx.obj[FILENAME] = {
        "rabbitmq_url": rabbitmq_url,
    }
    logger.debug("rabbitmq setup complete")
