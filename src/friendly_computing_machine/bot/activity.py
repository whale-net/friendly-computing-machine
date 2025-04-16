from temporalio import activity

from friendly_computing_machine.db.dal import get_genai_texts_by_slack_channel
from friendly_computing_machine.models.genai import GenAIText


@activity.defn
async def get_slack_channel_context(slack_channel_slack_id: str) -> list[GenAIText]:
    texts = get_genai_texts_by_slack_channel(slack_channel_slack_id)
    return texts


@activity.defn
async def generate_context_prompt(
    prompt_text: str,
    previous_context: str,
) -> str:
    """
    Generate a context prompt based on previous messages and the current prompt.
    """

    context_prompt = (
        "Here is the previous genAI requests:\n"
        f"{previous_context}\n"
        "\n"
        "Here is the new prompt you will need to respond to. \n"
        "Please consider the previous topics when responding, but don't make mention of them. "
        "Additionally, your response should not be too long. Ideally around 100-150 words, "
        "but you can go with more if needed. If the user specifies that it should be a long response, "
        "then feel free to disregard the response length restriction entirely.\n"
        "prompt:\n"
        f"{prompt_text}"
    )
    return context_prompt
