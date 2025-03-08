import logging
from datetime import datetime, timedelta

from friendly_computing_machine.bot.app import get_bot_config
from friendly_computing_machine.bot.task.abstracttask import ScheduledAbstractTask
from friendly_computing_machine.bot.util import slack_send_message
from friendly_computing_machine.db.dal import insert_music_poll_instance
from friendly_computing_machine.models.task import TaskInstanceStatus

logger = logging.getLogger(__name__)


class MusicPollPostPoll(ScheduledAbstractTask):
    OLD_TEMPLATE: str = """:catjam: `IT'S` :catjam: `CAT` :catjam: `JAM` :catjam: `TIME` :catjam:

:arrow_down_small: Post a song in the thread below :thread: :arrow_down_small: :whale:
"""

    def _run(self) -> TaskInstanceStatus:
        # TODO - templates from db

        # it is convenient to have same shared cache-type object as the event listener thread
        config = get_bot_config()
        logger.info("music poll info %s", config.music_poll_infos)
        for poll_info in config.music_poll_infos:
            # pick up last, if any, will mark as closed
            insert_music_poll_instance(poll_info.music_poll.to_instance())
            slack_send_message(
                poll_info.slack_channel.slack_id, ":catjam: any cat jammers? :catjam:"
            )
            # No need to start thread anymore
            # slack_send_message(
            #     channel_slack_id, ":thread: starter", thread_ts=base_message.ts
            # )

        return TaskInstanceStatus.OK

    @property
    def period(self) -> timedelta:
        return timedelta(days=7)

    @property
    def start_date(self) -> datetime:
        return datetime(2024, 11, 30)
