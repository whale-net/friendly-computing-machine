import logging

from temporalio import activity

from friendly_computing_machine.db.jobsql import (
    backfill_slack_messages_slack_channel_id,
    backfill_slack_messages_slack_team_id,
    backfill_slack_messages_slack_user_id,
)

logger = logging.getLogger(__name__)


@activity.defn
def backfill_slack_messages_slack_user_id_activity():
    """Backfills slack messages with slack user IDs."""
    logger.info("starting slack user id backfill")
    backfill_slack_messages_slack_user_id()
    return "OK"


@activity.defn
def backfill_slack_messages_slack_channel_id_activity():
    """Backfills slack messages with slack channel IDs."""
    logger.info("starting slack channel id backfill")
    backfill_slack_messages_slack_channel_id()
    return "OK"


@activity.defn
def backfill_slack_messages_slack_team_id_activity():
    """Backfills slack messages with slack team IDs."""
    logger.info("starting slack team id backfill")
    backfill_slack_messages_slack_team_id()
    return "OK"
