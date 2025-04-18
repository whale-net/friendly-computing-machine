from concurrent.futures import ThreadPoolExecutor
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)
from friendly_computing_machine.gemini.activity import (
    generate_gemini_response,
    generate_summary,
)
from friendly_computing_machine.bot.activity import (
    generate_context_prompt,
    get_slack_channel_context,
)
from friendly_computing_machine.bot.workflow import SlackConextGeminiWorkflow
from friendly_computing_machine.workflows.sample import (
    say_hello,
    SayHello,
    build_hello_prompt,
)
from friendly_computing_machine.workflows.util import (
    get_temporal_client_async,
    get_temporal_queue_name,
)


WORKFLOWS = [SayHello, SlackConextGeminiWorkflow]
ACTIVITIES = [
    generate_context_prompt,
    get_slack_channel_context,
    say_hello,
    generate_gemini_response,
    build_hello_prompt,
    generate_summary,
]


async def run_worker(app_env: str):
    # Create client connected to server at the given address
    # TODO - use common function
    client = await get_temporal_client_async()

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
