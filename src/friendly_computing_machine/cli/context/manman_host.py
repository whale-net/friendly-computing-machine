import logging
import os
from enum import Enum
from typing import Annotated

import typer

# Import the new ManManAPI class
from friendly_computing_machine.manman.api import ManManStatusAPI, OldManManAPI

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)


class SupportedAPI(Enum):
    old = "old"
    status = "status"


T_manman_host_url = Annotated[str, typer.Option(..., envvar="MANMAN_HOST_URL")]


def setup_old_manman_api(
    ctx: typer.Context,
    manman_host_url: T_manman_host_url,
):
    # Initialize the ManManAPI using the provided URL
    manman_host_url = manman_host_url.strip()
    # remove trailing slashes
    manman_host_url = manman_host_url.rstrip("/")
    OldManManAPI.init(manman_host_url)
    logger.info(f"ManMan API initialized with host: {manman_host_url}")
    ctx.obj.setdefault(FILENAME, {})[SupportedAPI.old] = OldManManAPI


def setup_manman_status_api(
    ctx: typer.Context,
    url: T_manman_host_url,
):
    """
    Setup the ManMan status API.
    This is a placeholder function for future implementation.
    """
    url = url.strip()
    # remove trailing slashes
    url = url.rstrip("/")
    ManManStatusAPI.init(url)
    # Here you would initialize the status API if it were implemented
    logger.info(f"ManMan Status API initialized with host: {url}")
    ctx.obj.setdefault(FILENAME, {})[SupportedAPI.status] = ManManStatusAPI
