from dataclasses import dataclass
import logging
import os


from typing import Annotated

import typer

from friendly_computing_machine.workflows.util import init_temporal

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)

T_temporal_host = Annotated[str, typer.Option(..., envvar="TEMPORAL_HOST")]


@dataclass
class TemporalConfig:
    host: str
    # TODO - queue names?


def setup_temporal(
    ctx: typer.Context,
    temporal_host: T_temporal_host,
):
    logger.debug("temporal client setup starting")
    init_temporal(
        host=temporal_host,
    )
    ctx.obj[FILENAME] = TemporalConfig(
        host=temporal_host,
    )
    logger.debug("temporal client setup complete")
