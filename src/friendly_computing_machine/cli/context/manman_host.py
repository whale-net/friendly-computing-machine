import logging
import os
from typing import Annotated

import typer

# Import the new ManManAPI class
from friendly_computing_machine.manman.util import ManManAPI

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)

T_manman_host_url = Annotated[str, typer.Option(..., envvar="MANMAN_HOST_URL")]


def setup_manman_host_api(
    ctx: typer.Context,
    manman_host_url: T_manman_host_url,
):
    # Initialize the ManManAPI using the provided URL
    manman_host_url = manman_host_url.strip()
    # remove trailing slashes
    manman_host_url = manman_host_url.rstrip("/")
    ManManAPI.init(manman_host_url)
    logger.info(f"ManMan API initialized with host: {manman_host_url}")
    # Store the URL in the context if needed elsewhere, though direct use of ManManAPI.get_client() is preferred
    ctx.obj[FILENAME] = manman_host_url
