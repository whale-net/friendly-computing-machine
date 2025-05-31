import logging
import os
from dataclasses import dataclass
from typing import Annotated, Optional

import typer

from friendly_computing_machine.cli.context.app_env import FILENAME as APP_ENV_FILENAME
from friendly_computing_machine.cli.context.app_env import T_app_env, setup_app_env
from friendly_computing_machine.temporal.util import init_temporal

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)

T_temporal_host = Annotated[str, typer.Option(..., envvar="TEMPORAL_HOST")]
T_temporal_org = Annotated[str, typer.Option("fcm", envvar="TEMPORAL_ORG", help="Organization identifier for workflow naming")]
T_temporal_app = Annotated[str, typer.Option("friendly-computing-machine", envvar="TEMPORAL_APP", help="Application name for workflow naming")]


@dataclass
class TemporalConfig:
    host: str
    org: str
    app: str
    # TODO - queue names?


def setup_temporal(
    ctx: typer.Context,
    temporal_host: T_temporal_host,
    app_env: T_app_env,
    temporal_org: T_temporal_org = "fcm",
    temporal_app: T_temporal_app = "friendly-computing-machine",
):
    """
    Set up temporal client with standardized naming configuration.
    
    Args:
        ctx: Typer context
        temporal_host: Temporal server host
        app_env: Environment (dev, staging, prod, etc.)
        temporal_org: Organization identifier for naming
        temporal_app: Application name for naming
    """
    logger.debug("temporal client setup starting")
    setup_app_env(ctx, app_env)
    
    env = ctx.obj[APP_ENV_FILENAME]["app_env"]
    
    # Initialize temporal with new naming system
    init_temporal(
        host=temporal_host,
        app_env=env,
        org=temporal_org,
        app=temporal_app,
    )
    
    ctx.obj[FILENAME] = TemporalConfig(
        host=temporal_host,
        org=temporal_org,
        app=temporal_app,
    )
    
    logger.info(
        "temporal client setup complete: host=%s, env=%s, org=%s, app=%s",
        temporal_host, env, temporal_org, temporal_app
    )
