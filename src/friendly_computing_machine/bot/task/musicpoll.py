import logging
from datetime import datetime, timedelta, UTC

from friendly_computing_machine.bot.app import get_bot_config, get_slack_web_client
from friendly_computing_machine.bot.task.abstracttask import (
    ScheduledAbstractTask,
    OneOffTask,
    AbstractTask,
)
from friendly_computing_machine.bot.util import slack_send_message
from friendly_computing_machine.db.dal import insert_music_poll_instance, upsert_message
from friendly_computing_machine.db.jobsql import (
    backfill_init_music_polls,
    backfill_init_music_poll_instances,
    backfill_music_poll_instance_next_id,
)
from friendly_computing_machine.models.task import TaskInstanceStatus
from friendly_computing_machine.models.slack import SlackMessageCreate

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
            logger.info("sent poll message id=%s", poll_message.id)
            insert_music_poll_instance(
                poll_info.music_poll.to_instance(poll_message.id)
            )

            backfill_music_poll_instance_next_id()

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


class MusicPollArchiveMessages(AbstractTask):
    """
    Archive the messages in the music poll channels
    """

    @property
    def period(self) -> timedelta:
        return timedelta(days=1)

    def _run(self) -> TaskInstanceStatus:
        bot_config = get_bot_config(should_ignore_cache=True)
        # TODO - this is the same logic as the event handler for now
        archive_channel_slack_ids = {
            info.slack_channel.slack_id for info in bot_config.music_poll_infos
        }

        slack_client = get_slack_web_client()
        # free slack is 90 days, no need for more
        # one less to avoid any odd off by one errors
        search_start_unix_timestamp = (
            datetime.now(UTC) - timedelta(days=89)
        ).timestamp()
        for channel_slack_id in archive_channel_slack_ids:
            response = slack_client.conversations_history(channel=channel_slack_id)
            messages = response["messages"]
            while len(messages) > 0:
                upserted_message_ids = []
                for message in messages:
                    # upsert the message
                    slack_message_create = SlackMessageCreate.from_slack_message_json(
                        message,
                        # specify because we pulled it down and I don't think it's included in the response
                        slack_channel_slack_id=channel_slack_id,
                    )
                    slack_message = upsert_message(slack_message_create)
                    logger.debug("upserted message %s", slack_message.id)
                    upserted_message_ids.append(slack_message.id)
                logger.info("finished batch of messages %s", upserted_message_ids)

                # get the next batch
                oldest_ts = min(map(lambda msg: msg["ts"], messages))
                if float(oldest_ts) < search_start_unix_timestamp:
                    logger.info(
                        "reached message %s before search start timestamp %s",
                        oldest_ts,
                        search_start_unix_timestamp,
                    )
                    break
                response = slack_client.conversations_history(
                    channel=channel_slack_id,
                    latest=oldest_ts,
                )
                messages = response["messages"]

        return TaskInstanceStatus.OK
