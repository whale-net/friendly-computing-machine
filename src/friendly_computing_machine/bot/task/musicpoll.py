from datetime import timedelta, datetime

from friendly_computing_machine.bot.task.abstracttask import ScheduledAbstractTask
from friendly_computing_machine.bot.app import get_bot_config
from friendly_computing_machine.models.task import TaskInstanceStatus
from friendly_computing_machine.bot.util import slack_send_message


class MusicPollPostPoll(ScheduledAbstractTask):
    TEMPLATE: str = """:catjam: `IT'S` :catjam: `CAT` :catjam: `JAM` :catjam: `TIME` :catjam:

:arrow_down_small: Post a song in the thread below :thread: :arrow_down_small: :whale:
"""

    def _run(self) -> TaskInstanceStatus:
        # TODO - templates from db

        # this is a bit of an anti-pattern but whatever (for now)
        # it is convenient to have same shared cache-type object as the event listener thread
        config = get_bot_config()
        for channel_slack_id in config.MUSIC_POLL_CHANNEL_IDS:
            base_message = slack_send_message(
                channel_slack_id, MusicPollPostPoll.TEMPLATE
            )
            slack_send_message(
                channel_slack_id, ":thread: starter", thread_ts=base_message.ts
            )

        return TaskInstanceStatus.EXCEPTION

    @property
    def period(self) -> timedelta:
        return timedelta(days=7)

    @property
    def start_date(self) -> datetime:
        return datetime(2024, 11, 29)
