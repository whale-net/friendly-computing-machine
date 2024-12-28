import functools
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

from slack_bolt import App
from slack_sdk import WebClient

from friendly_computing_machine.db.dal import (
    get_bot_slack_user_slack_ids,
    get_music_poll_channel_slack_ids,
)

__GLOBALS = {}


logger = logging.getLogger(__name__)
bot_config_lock = Lock()


class SlackWebClientFCM(WebClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @functools.cached_property
    def team_id(self) -> str:
        """
        :return: returns cached current team_id
        """
        team_info_response = self.team_info()
        if team_info_response.status_code != 200:
            raise RuntimeError("status_code not 200 team_info_response")
        return team_info_response.get("team").get("id")


def init_client():
    if "slack_web_client" in __GLOBALS:
        raise RuntimeError("double slack web client init")
    __GLOBALS["slack_web_client"] = SlackWebClientFCM(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        logger=logging.getLogger("slack_web"),
    )


if os.environ.get("SKIP_SLACK_APP_INIT") == "ya":
    # we don't always want to spawn a slack app (migrations)
    # need to figure out better way to do this, but for now it works
    # the magic mock is to just make all decorator stuff work because this is structured poorly
    from unittest.mock import MagicMock

    app = MagicMock()
else:
    app = App(client=init_client(), logger=logging.getLogger("slack_bolt"))


@dataclass
class SlackBotConfig:
    MUSIC_POLL_CHANNEL_IDS: set[str]
    BOT_SLACK_USER_IDS: set[str]
    as_of: datetime

    REFRESH_PERIOD: timedelta = timedelta(minutes=1)

    @classmethod
    def create(cls):
        return SlackBotConfig(
            MUSIC_POLL_CHANNEL_IDS=get_music_poll_channel_slack_ids(),
            BOT_SLACK_USER_IDS=get_bot_slack_user_slack_ids(),
            as_of=datetime.now(),
        )


def get_bot_config() -> SlackBotConfig:
    # assuming that this function is not thread safe when called by bolt and adding a lock
    # TODO - improve config access
    if not bot_config_lock.acquire(timeout=10):
        raise RuntimeError("bot lock timeout")
    config = __GLOBALS.get("bot_config")
    if config is None:
        logger.info("creating slackbot config for the first time")
        config = SlackBotConfig.create()
    elif config.as_of + SlackBotConfig.REFRESH_PERIOD < datetime.now():
        logger.info("slackbot config has expired, refreshing")
        config = SlackBotConfig.create()
    __GLOBALS["bot_config"] = config
    bot_config_lock.release()
    return config


def get_client() -> SlackWebClientFCM:
    client = __GLOBALS.get("slack_web_client")
    if client is None:
        raise RuntimeError("client not init")
    return client
