import logging
from typing import Optional

from sqlmodel import text, Session
from friendly_computing_machine.db.db import SessionManager

logger = logging.getLogger(__name__)


def backfill_init_music_polls() -> None:
    """
    Backfill the music polls from the slack messages
    """
    with SessionManager() as session:
        session.execute(
            text("""
            insert into fcm.musicpoll(slack_channel_id, start_date, name)
            select id, '2024-11-30 19:00:00', 'auto generated poll from migration'
            from fcm.slackchannel sc
            where sc.is_music_poll
                and not exists (select * from fcm.musicpoll mp2 where mp2.slack_channel_id = sc.id)
        """)
        )
        session.commit()


def backfill_init_music_poll_instances() -> None:
    """
    Backfill the music poll instances from the slack messages
    """
    with SessionManager() as session:
        session.execute(
            text("""
            insert into fcm.musicpollinstance(music_poll_id, slack_message_id, created_at)
            select mp.id, sm.id,sm.ts
            from fcm.slackchannel sc
                     inner join fcm.musicpoll mp on sc.id = mp.slack_channel_id
                     inner join fcm.slackmessage sm on sc.id = sm.slack_channel_id
            where sm.slack_user_id in
                  (select id
                   from fcm.slackuser
                   where is_bot
                  )
            -- ignore child messages
              and sm.thread_ts is null
              and sc.is_music_poll
              and sm.ts >= mp.start_date
              and not exists (
                select *
                from fcm.musicpollinstance mpi2
                where mpi2.music_poll_id = mp.id
                  and mpi2.created_at = sm.ts
            )
            order by sm.ts
        """)
        )

        backfill_music_poll_instance_next_id(session)


def backfill_music_poll_instance_next_id(in_session: Optional[Session] = None):
    # TODO - this may become non-performant with large data sets
    # but this is also unlikely to ever be a large dataset
    with SessionManager(in_session) as session:
        session.execute(
            text("""
                with next_ids as (
                    select
                        id,
                        lead(id, 1) over (partition by music_poll_id order by created_at) as next_id
                    from fcm.musicpollinstance
                )
                update fcm.musicpollinstance mpi
                set next_instance_id = next_ids.next_id
                from next_ids
                where mpi.id = next_ids.id
                  and mpi.next_instance_id is null
            """)
        )
        session.commit()


def delete_slack_message_duplicates():
    with SessionManager() as session:
        # too lazy to redo with sqlmodel
        slack_id_dupe_count = session.execute(
            text("""
        delete from fcm.slackmessage sm
        where slack_id is not null
        and exists
            (select *
            from fcm.slackmessage sm2
            -- trusting that this is truly globally unique at slack
            -- otherwise, need to add ts or something
            where sm2.slack_id = sm.slack_id
            and sm2.id < sm.id
            )
        """)
        ).rowcount
        slack_ts_dupe_count = session.execute(
            text("""
        delete from fcm.slackmessage sm
        where exists
            (select *
            from fcm.slackmessage sm2
            where sm2.slack_team_slack_id = sm.slack_team_slack_id
            and sm2.slack_channel_slack_id = sm.slack_channel_slack_id
            and sm2.ts = sm.ts
            and sm2.id < sm.id
            )
        """)
        ).rowcount
        session.commit()
        logger.info(
            "slack_id_dupe_count=%s slack_ts_dupe_count=%s total=%s",
            slack_id_dupe_count,
            slack_ts_dupe_count,
            slack_id_dupe_count + slack_ts_dupe_count,
        )
