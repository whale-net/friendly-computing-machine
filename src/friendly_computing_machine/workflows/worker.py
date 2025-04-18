import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from friendly_computing_machine.bot.activity import (
    backfill_slack_user_info_activity,
    generate_context_prompt,
    get_slack_channel_context,
)
from friendly_computing_machine.bot.workflow import (
    SlackConextGeminiWorkflow,
    SlackMessageQODWorkflow,
    SlackUserInfoWorkflow,
)
from friendly_computing_machine.db.job_activity import (
    backfill_slack_messages_slack_channel_id_activity,
    backfill_slack_messages_slack_team_id_activity,
    backfill_slack_messages_slack_user_id_activity,
    backfill_teams_from_messages_activity,
    delete_slack_message_duplicates_activity,
    upsert_slack_user_creates_activity,
)
from friendly_computing_machine.gemini.activity import (
    generate_gemini_response,
    generate_summary,
)
from friendly_computing_machine.workflows.base import AbstractScheduleWorkflow
from friendly_computing_machine.workflows.sample import (
    SayHello,
    build_hello_prompt,
    say_hello,
)
from friendly_computing_machine.workflows.util import (
    get_temporal_client_async,
    get_temporal_queue_name,
)

logger = logging.getLogger(__name__)


WORKFLOWS = [
    SayHello,
    SlackConextGeminiWorkflow,
    SlackMessageQODWorkflow,
    SlackUserInfoWorkflow,
]
ACTIVITIES = [
    generate_context_prompt,
    get_slack_channel_context,
    say_hello,
    generate_gemini_response,
    build_hello_prompt,
    generate_summary,
    backfill_slack_messages_slack_user_id_activity,
    backfill_slack_messages_slack_channel_id_activity,
    backfill_slack_messages_slack_team_id_activity,
    backfill_slack_user_info_activity,
    backfill_teams_from_messages_activity,
    delete_slack_message_duplicates_activity,
    upsert_slack_user_creates_activity,
]


async def run_worker(app_env: str):
    # Create client connected to server at the given address
    client = await get_temporal_client_async()

    # create schedules for schedule workflows
    futures = []
    for wf in WORKFLOWS:
        if not issubclass(wf, AbstractScheduleWorkflow):
            continue
        futures.append(wf().async_upsert_schedule(client, app_env))
    asyncio.gather(*futures)
    logger.info("all schedules created")

    # Run the worker
    with ThreadPoolExecutor(max_workers=100) as activity_executor:
        runner = SandboxedWorkflowRunner(
            # restrictions=SandboxRestrictions.default.with_passthrough_modules("slack_sdk"),
            # TODO - actually ifgure out what is not deterministic
            # it is slack calls, but from where?
            restrictions=SandboxRestrictions.default.with_passthrough_all_modules(),
        )
        worker = Worker(
            client,
            task_queue=get_temporal_queue_name("main"),
            workflows=WORKFLOWS,
            activities=ACTIVITIES,
            activity_executor=activity_executor,
            workflow_runner=runner,
        )
        await worker.run()
