import functools
import os
from datetime import datetime, timedelta
from dataclasses import dataclass

from slack_bolt import App
from slack_sdk import WebClient

from friendly_computing_machine.db.dal import (
    get_music_poll_channel_slack_ids,
    get_bot_slack_user_slack_ids,
)

__GLOBALS = {}


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
        token=os.environ.get("SLACK_BOT_TOKEN"), logger=None
    )


if os.environ.get("SKIP_SLACK_APP_INIT") == "ya":
    from unittest.mock import MagicMock

    app = MagicMock()
else:
    app = App(client=init_client())


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
    config = __GLOBALS.get("bot_config")
    if config is None:
        config = SlackBotConfig.create()
    elif config.as_of + SlackBotConfig.REFRESH_PERIOD < datetime.now():
        config = SlackBotConfig.create()

    return config


def get_client() -> SlackWebClientFCM:
    client = __GLOBALS.get("slack_web_client")
    if client is None:
        raise RuntimeError("client not init")
    return client
