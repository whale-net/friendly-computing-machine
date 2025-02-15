import logging
from textwrap import dedent

import google.generativeai as genai

from friendly_computing_machine.cli.util import CliContext
from friendly_computing_machine.db.dal import get_genai_texts_by_slack_channel

logger = logging.getLogger(__name__)


def init():
    context = CliContext.get_instance()
    genai.configure(api_key=context.google_api_key)


def generate_text_with_slack_context(
    user_name: str, prompt_text: str, slack_channel_slack_id: str
):
    previous_messages = get_genai_texts_by_slack_channel(slack_channel_slack_id)

    # if this works make generic? are there libraries for things like this?
    previous_inputs = []
    for msg in reversed(previous_messages):
        previous_inputs.append(
            dedent(f"""
        <input>
        <prompt>
        {msg.prompt}
        </prompt>
        <response>
        {msg.response or ''}
        </response>
        </input>
        """)
        )

    # does this work?
    context_prompt = dedent("""
        You are going to prepare a response for a request that is likely silly.
        Here are some of the previous prompts that you may want to consider, but also, may not want to consider.
        I'll leave it to your discretion to consider if the previous prompts are relevant.
        If they are inappropriate please remove them from the request.
        <previous_inputs>
        {{previous_inputs}}
        </previous_inputs>

        Here is the actual prompt you need to respond to, but do still consider the above previous inputs:
    """).replace("{{previous_inputs}}", "\n".join(previous_inputs))

    generated_prompt = context_prompt + f"\n{prompt_text}"
    return generate_text(user_name, generated_prompt)


def generate_text(user_name: str, prompt_text: str) -> tuple:
    try:
        # TODO - model name - using default for now
        model = genai.GenerativeModel()
        logger.info("about to generate response for %s", prompt_text)
        response = model.generate_content(prompt_text)

        response_text = response.text
        # Check for prompt feedback (e.g., blocked due to safety settings)
        is_safe = True
        if response.prompt_feedback:
            logger.info(f"Prompt Feedback: {response.prompt_feedback}")

            feedback_prompt = dedent("""
                You are an AI agent tasked with handling the worst prompts humanity can provide you.
                You are writing rejection letters for invalid prompts. Here is a sample prompt, but please expand on it as you see fit.
                This is intended to be a for-fun app.

                <prompt>
                Listen here bucko, your prompt was INAPPROPRIATE. Do you really think this is a game?
                This is a STATE OF THE ART MULTIMODAL AI!!!! Do you think anyone else really has access to this? Thought so...
                Anyways, try again, with cleaner language.

                I'm watching you {user_name}
                </prompt>
            """)

            # You might want to handle blocked prompts differently, e.g.,
            # by informing the user or modifying the prompt.
            feedback_response = model.generate_content(
                feedback_prompt.replace("{user_name}", user_name)
            )
            response_text = feedback_response.text or feedback_response.prompt_feedback
            is_safe = False

        logger.info("response generated, is_safe=%s", is_safe)
        # TODO - safety rating retrieval
        # Extract and return the generated text, prompt feedback, and safety ratings
        return response_text, response.prompt_feedback  # , response.safety_ratings

    except Exception as e:
        logger.info(f"An error occurred: {e}")
        return None, None  # , None
