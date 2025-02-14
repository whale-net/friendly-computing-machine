import logging
import google.generativeai as genai

from friendly_computing_machine.cli.util import CliContext

logger = logging.getLogger(__name__)

feedback_prompt = """
You are an AI agent tasked with handling the worst prompts humanity can provide you.
You are writing rejection letters for invalid prompts. Here is a sample prompt, but please expand on it as you see fit.
This is intended to be a for-fun app.

<prompt>
Listen here bucko, your prompt was INAPPROPRIATE. Do you really think this is a game?
This is a STATE OF THE ART MULTIMODAL AI!!!! Do you think anyone else really has access to this? Thought so...
Anyways, try again, with cleaner language.

I'm watching you {user_name}
</prompt>
"""


def init():
    context = CliContext.get_instance()
    genai.configure(api_key=context.google_api_key)


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
            print(f"Prompt Feedback: {response.prompt_feedback}")
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
