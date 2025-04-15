from concurrent.futures import ThreadPoolExecutor
from temporalio.client import Client
from temporalio.worker import Worker
from friendly_computing_machine.gemini.activity import generate_gemini_response
from friendly_computing_machine.workflows.sample import (
    say_hello,
    SayHello,
    build_hello_prompt,
)

WORKFLOWS = [SayHello]
ACTIVITIES = [say_hello, generate_gemini_response, build_hello_prompt]


async def run_worker(host: str):
    # Create client connected to server at the given address
    client = await Client.connect(host)

    # Run the worker
    with ThreadPoolExecutor(max_workers=100) as activity_executor:
        # not useufl anymore
        # runner = SandboxedWorkflowRunner(
        #     restrictions=SandboxRestrictions.default.with_passthrough_modules("slack_sdk"),
        #     restrictions=SandboxRestrictions.default.with_passthrough_all_modules(),
        # )
        worker = Worker(
            client,
            task_queue="my-task-queue",
            workflows=WORKFLOWS,
            activities=ACTIVITIES,
            activity_executor=activity_executor,
            # workflow_runner=runner,
        )
        await worker.run()
