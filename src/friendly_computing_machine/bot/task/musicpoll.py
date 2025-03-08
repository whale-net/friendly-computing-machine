import logging
from datetime import datetime, timedelta

from friendly_computing_machine.bot.app import get_bot_config
from friendly_computing_machine.bot.task.abstracttask import (
    ScheduledAbstractTask,
    OneOffTask,
)
from friendly_computing_machine.bot.util import slack_send_message
from friendly_computing_machine.db.dal import insert_music_poll_instance
from friendly_computing_machine.db.jobsql import (
    backfill_init_music_polls,
    backfill_init_music_poll_instances,
)
from friendly_computing_machine.models.task import TaskInstanceStatus

logger = logging.getLogger(__name__)


class MusicPollPostPoll(ScheduledAbstractTask):
    OLD_TEMPLATE: str = """:catjam: `IT'S` :catjam: `CAT` :catjam: `JAM` :catjam: `TIME` :catjam:

:arrow_down_small: Post a song in the thread below :thread: :arrow_down_small: :whale:
"""

    def _run(self) -> TaskInstanceStatus:
        # TODO - templates from db

        # it is convenient to have same shared cache-type object as the event listener thread
        # ignore cache, since this job runs less frequently
        config = get_bot_config(should_ignore_cache=True)
        logger.info("music poll info %s", config.music_poll_infos)
        for poll_info in config.music_poll_infos:
            poll_message = slack_send_message(
                poll_info.slack_channel.slack_id, ":catjam: any cat jammers? :catjam:"
            )
            insert_music_poll_instance(
                poll_info.music_poll.to_instance(poll_message.id)
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


class MusicPollInit(OneOffTask):
    """
    The music poll response logging was added before any musicpoll database stuff was added.
    So this will initialize the database with the past polls
    """

    def _run(self) -> TaskInstanceStatus:
        backfill_init_music_polls()
        logger.info("music poll backfilled for init")
        backfill_init_music_poll_instances()
        logger.info("music poll instance backfilled for init")
        return TaskInstanceStatus.OK
