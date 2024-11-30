from datetime import timedelta

from friendly_computing_machine.models.slack import SlackUserCreate
from friendly_computing_machine.models.task import TaskInstanceStatus

from friendly_computing_machine.bot.task.abstracttask import AbstractTask
from friendly_computing_machine.db.dal import (
    select_distinct_slack_user_slack_id_from_slack_message,
    upsert_slack_users,
)


class FindUsers(AbstractTask):
    @property
    def period(self) -> timedelta:
        return timedelta(minutes=5)

    def _run(self) -> TaskInstanceStatus:
        slack_user_slack_ids = select_distinct_slack_user_slack_id_from_slack_message()
        slack_user_creates = [
            SlackUserCreate(
                slack_id=slack_user_id,
                name="TODO",
            )
            for slack_user_id in slack_user_slack_ids
        ]

        print(upsert_slack_users(slack_user_creates))

        return TaskInstanceStatus.OK
