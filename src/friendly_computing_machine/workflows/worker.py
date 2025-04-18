import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import ScheduleAlreadyRunningError
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from friendly_computing_machine.bot.activity import (
    generate_context_prompt,
    get_slack_channel_context,
)
from friendly_computing_machine.bot.workflow import (
    SlackConextGeminiWorkflow,
    SlackMessageQODWorkflow,
)
from friendly_computing_machine.db.job_activity import (
    backfill_slack_messages_slack_channel_id_activity,
    backfill_slack_messages_slack_team_id_activity,
    backfill_slack_messages_slack_user_id_activity,
)
from friendly_computing_machine.gemini.activity import (
    generate_gemini_response,
    generate_summary,
)
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


WORKFLOWS = [SayHello, SlackConextGeminiWorkflow, SlackMessageQODWorkflow]
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
]


async def run_worker(app_env: str):
    # Create client connected to server at the given address
    client = await get_temporal_client_async()

    # create schedules
    test_wf = SlackMessageQODWorkflow()
    try:
        await client.create_schedule(
            # Hardcoded for now, but should be dynamic from workflow list
            # additionally, it is weird to instantiate the workflow here
            # but it is the only way to get the schedule
            # still not familiar with the lifecycle of the workflow member vars
            # in this temporal land
            test_wf.get_schedule_id(app_env),
            test_wf.get_schedule(app_env),
        )
    except ScheduleAlreadyRunningError as e:
        logger.info("%s - schedule already running", e)

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
