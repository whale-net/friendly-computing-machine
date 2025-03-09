import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from friendly_computing_machine.bot.app import (
    get_bot_config,
    get_slack_web_client,
    SlackWebClientFCM,
)
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
    delete_slack_message_duplicates,
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
        delete_slack_message_duplicates()

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
            MusicPollArchiveMessages._archive_slack_channel(
                channel_slack_id,
                slack_client,
                max_ts_offset=search_start_unix_timestamp,
            )

        return TaskInstanceStatus.OK

    @staticmethod
    def _archive_slack_channel(
        slack_channel_slack_id: str,
        slack_client: SlackWebClientFCM,
        max_ts_offset: Optional[None] = None,
    ) -> None:
        if max_ts_offset is None:
            # 30 day lookback by default, should be enough
            # gives 30 days to catch this
            max_ts_offset = (datetime.now(UTC) - timedelta(days=30)).timestamp()

        def archive_message_batch(
            m_batch, t_batch
        ) -> tuple[list[dict], list[dict], list[int]]:
            """
            Archive a batch of messages
            :param m_batch: message batch incoming
            :param t_batch: thread batch incoming
            :return:
            """
            ids = []
            thread_batch = []
            msg_batch = m_batch + t_batch
            for msg in msg_batch:
                # upsert the message
                create = SlackMessageCreate.from_slack_message_json(
                    msg,
                    # specify because we pulled it down and I don't think it's included in the response
                    slack_channel_slack_id=slack_channel_slack_id,
                )
                # this is too much info but was useful for debug, although not useful enough
                # logger.info('upserting message %s %s %s', create.slack_id, create.ts, create.text)
                message_instance = upsert_message(create)
                ids.append(message_instance.id)
                logger.info("upserted message %s", message_instance.id)

                # if this is a thread message, pick up replies
                if msg.get("thread_ts") is not None and msg.get("ts") == msg.get(
                    "thread_ts"
                ):
                    message_replies = slack_client.conversations_replies(
                        channel=slack_channel_slack_id,
                        ts=msg.get("thread_ts"),
                    )
                    # remove the root thread message from this batch
                    reply_messages = [
                        message
                        for message in (message_replies["messages"] or [])
                        if message.get("ts") != msg.get("thread_ts")
                    ]
                    logger.info("found %s thread messages", len(reply_messages))
                    thread_batch += reply_messages

            # get the next batch
            # if we have no messages, we are done
            oldest_ts = (
                min(map(lambda msg: float(msg["ts"]), m_batch))
                if len(m_batch) > 0
                else max_ts_offset
            )
            next_fetch = MusicPollArchiveMessages._fetch_slack_messages(
                slack_channel_slack_id,
                slack_client,
                oldest_ts=max_ts_offset,
                latest_ts=oldest_ts,
            )
            logger.info("fetched %s messages", len(next_fetch))
            return next_fetch, thread_batch, ids

        message_batch = MusicPollArchiveMessages._fetch_slack_messages(
            slack_channel_slack_id,
            slack_client,
            oldest_ts=max_ts_offset,
        )
        thread_batch = []
        while len(message_batch) > 0 or len(thread_batch) > 0:
            message_batch, thread_batch, updated_ids = archive_message_batch(
                message_batch, thread_batch
            )
            logger.info("bulk upserted %s messages", len(updated_ids))

    @staticmethod
    def _fetch_slack_messages(
        slack_channel_slack_id: str,
        slack_client: SlackWebClientFCM,
        oldest_ts: float,
        latest_ts: Optional[float | str] = None,
    ) -> list[dict]:
        if oldest_ts == latest_ts:
            return []
        response = slack_client.conversations_history(
            channel=slack_channel_slack_id,
            latest=str(latest_ts) if latest_ts is not None else None,
            oldest=str(oldest_ts),
        )
        return response["messages"] or []
