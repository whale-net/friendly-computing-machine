from textwrap import dedent

import google.generativeai as genai
from temporalio import activity

from friendly_computing_machine.models.genai import GenAIText


async def gen_text(prompt: str) -> str:
    """
    Generate text using the Gemini AI model.
    """
    model = genai.GenerativeModel()
    response = await model.generate_content_async(prompt)
    return response.text


@activity.defn
async def generate_gemini_response(
    prompt_text: str,
) -> str:
    """
    Generate a response using the Gemini AI model.
    """
    return await gen_text(prompt_text)


@activity.defn
async def generate_summary(messages: list[GenAIText]) -> str:
    """
    Generate a summary from a list of responses
    """
    summary_prompt = dedent("""
        Here is are the previous genAI requests:\n
    """)
    for msg in sorted(messages, key=lambda x: x.created_at):
        summary_prompt += dedent(f"""
            - message_{msg.id}:
                - prompt: "{msg.prompt}"
                - response: "{msg.response or ""}"
            """)
    summary_prompt += (
        "\n"
        "\n"
        "That concludes the previous genAI requests. "
        "Please summarize the important topics from these requests and responses."
        "This will be fed into another model as a seed prompt.\n"
        "Please produce the summary in list format. "
        "Please do not include any other text or formatting. "
        "Just the list of important topics.\n"
        "If requests or topics are repeated, emphasis can be placed on them."
    )
    return await gen_text(summary_prompt)


@activity.defn
async def get_vibe(prompt: str) -> str:
    """
    Generate a vibe using the Gemini AI model.
    """
    prompt = dedent("""
        Please figure out the vibe of this prompt:

        Please return a one sentence summary of the vibe. Please be as concise as possible.
        Please do not include any other text or formatting. Just the vibe.
    """)
    return await gen_text(prompt)


@activity.defn
async def detect_call_to_action(response: str) -> bool:
    """
    Detect if the AI response contains a call to action that should notify everyone.
    """
    detection_prompt = dedent(f"""
        Analyze the following AI response and determine if it contains a call to action
        that should notify all members of a Slack channel (with @here).

        A call to action that warrants @here includes:
        - Urgent announcements or requests
        - Time-sensitive opportunities
        - Important meetings or events requiring participation
        - Critical alerts or warnings
        - Requests for immediate feedback or input from the team

        Response to analyze:
        "{response}"

        Respond with only "YES" if this contains a call to action that should notify everyone,
        or "NO" if it does not. No other text or formatting.
    """)

    detection_result = await gen_text(detection_prompt)
    return detection_result.strip().upper() == "YES"
