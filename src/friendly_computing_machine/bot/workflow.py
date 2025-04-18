import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.client import ScheduleIntervalSpec, ScheduleSpec

from friendly_computing_machine.bot.activity import (
    GenerateContextPromptParams,
    generate_context_prompt,
    get_slack_channel_context,
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
from friendly_computing_machine.workflows.base import AbstractScheduleWorkflow

logger = logging.getLogger(__name__)


@dataclass
class SlackConextGeminiWorkflowParams:
    """
    Parameters for the SlackConextGeminiWorkflow.
    """

    slack_channel_slack_id: str
    prompt: str


@workflow.defn
class SlackConextGeminiWorkflow:
    """
    Workflow to generate a response using the Gemini AI model.
    This workflow is specifically designed to work with the Slack context.
    It retrieves the previous messages from the Slack channel and generates a response
    based on the provided prompt and the summarized context.
    """

    @workflow.run
    async def run(self, params: SlackConextGeminiWorkflowParams):
        slack_prompts = await workflow.execute_activity(
            get_slack_channel_context,
            params.slack_channel_slack_id,
            schedule_to_close_timeout=timedelta(seconds=60),
            start_to_close_timeout=timedelta(seconds=60),
        )
        summary = await workflow.execute_activity(
            generate_summary,
            slack_prompts,
            schedule_to_close_timeout=timedelta(seconds=60),
            start_to_close_timeout=timedelta(seconds=60),
        )

        # this is a hack to do something I don't know how to do
        # and doesn't really work, but it's at least a start
        # TODO - understand context
        context_prompt = await workflow.execute_activity(
            generate_context_prompt,
            GenerateContextPromptParams(params.prompt, summary),
            schedule_to_close_timeout=timedelta(seconds=60),
            start_to_close_timeout=timedelta(seconds=60),
        )
        response = await workflow.execute_activity(
            generate_gemini_response,
            context_prompt,
            schedule_to_close_timeout=timedelta(seconds=60),
            start_to_close_timeout=timedelta(seconds=60),
        )
        return response


@dataclass
class SlackMessageQODWorkflowParams:
    """
    Parameters for the SlackMessageQODWorkflow.
    """

    pass


@workflow.defn
class SlackMessageQODWorkflow(AbstractScheduleWorkflow):
    """
    Workflow to generate a response using the Gemini AI model.
    This workflow is specifically designed to work with the Slack context.
    It retrieves the previous messages from the Slack channel and generates a response
    based on the provided prompt and the summarized context.
    """

    def get_schedule_spec(self) -> ScheduleSpec:
        return ScheduleSpec(
            intervals=[ScheduleIntervalSpec(every=timedelta(minutes=2))],
        )

    @workflow.run
    async def run(
        self, params: SlackConextGeminiWorkflowParams = SlackMessageQODWorkflowParams()
    ):
        logger.info("params %s", params)

        channel_activity = workflow.start_activity(
            backfill_slack_messages_slack_channel_id_activity,
            start_to_close_timeout=timedelta(seconds=10),
        )
        user_activity = workflow.start_activity(
            backfill_slack_messages_slack_user_id_activity,
            start_to_close_timeout=timedelta(seconds=10),
        )
        team_activity = workflow.start_activity(
            backfill_slack_messages_slack_team_id_activity,
            start_to_close_timeout=timedelta(seconds=10),
        )
        results = await asyncio.gather(channel_activity, user_activity, team_activity)
        logger.info("results %s", results)

        return results
