from dataclasses import dataclass
from temporalio import workflow

from friendly_computing_machine.gemini.activity import (
    generate_gemini_response,
    generate_summary,
)
from friendly_computing_machine.bot.activity import (
    generate_context_prompt,
    get_slack_channel_context,
)


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
    async def run(params: SlackConextGeminiWorkflowParams):
        slack_prompts = await workflow.execute_activity(
            get_slack_channel_context, params.slack_channel_slack_id
        )
        summary = await workflow.execute_activity(generate_summary, slack_prompts)

        # this is a hack to do something I don't know how to do
        # and doesn't really work, but it's at least a start
        # TODO - understand context
        context_prompt = await workflow.execute_activity(
            generate_context_prompt, params.prompt, summary
        )
        response = await workflow.execute_activity(
            generate_gemini_response, context_prompt
        )
        return response
