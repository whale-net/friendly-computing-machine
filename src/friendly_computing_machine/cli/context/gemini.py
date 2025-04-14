import logging
import os


from typing import Annotated

import typer
import google.generativeai as genai

logger = logging.getLogger(__name__)
FILENAME = os.path.basename(__file__)

T_google_api_key = Annotated[str, typer.Option(..., envvar="GOOGLE_API_KEY")]


def setup_gemini(
    ctx: typer.Context,
    google_api_key: T_google_api_key,
):
    logger.debug("gemini setup starting")
    if google_api_key is None:
        logger.critical("google api key not set")
        raise RuntimeError("google api key not set")
    genai.configure(api_key=google_api_key)
    logger.debug("gemini setup complete")
    # mark true just so it's not None
    ctx.obj[FILENAME] = True
