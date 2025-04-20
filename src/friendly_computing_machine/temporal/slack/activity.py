import logging
from dataclasses import dataclass

from temporalio import activity

from friendly_computing_machine.bot.app import get_slack_web_client
from friendly_computing_machine.db.dal import (
    get_genai_texts_by_slack_channel,
    get_user_teams_from_messages,
)
from friendly_computing_machine.models.genai import GenAIText
from friendly_computing_machine.models.slack import SlackUserCreate

logger = logging.getLogger(__name__)


# TODO - put this in db.dal_activity (or just activity? or activity.dal and)
@activity.defn
async def get_slack_channel_context(slack_channel_slack_id: str) -> list[GenAIText]:
    texts = get_genai_texts_by_slack_channel(slack_channel_slack_id)
    return texts


@dataclass
class GenerateContextPromptParams:
    """
    Parameters for the generate_context_prompt activity.
    """

    prompt_text: str
    previous_context: str
    vibe: str


@activity.defn
async def generate_context_prompt(params: GenerateContextPromptParams) -> str:
    """
    Generate a context prompt based on previous messages and the current prompt.
    """

    context_prompt = (
        "Here is the vibe of the prompt you are about to receive:\n"
        f"{params.vibe}\n"
        "\n"
        "Please do the opposite of this vibe in your response, unless it appears to be sincere. \n"
        "\n"
        "Here is the previous genAI requests:\n"
        f"{params.previous_context}\n"
        "\n"
        "Here is the new prompt you will need to respond to. \n"
        "Please consider the previous topics when responding, but don't make mention of them. "
        "Additionally, your response should not be too long. Ideally around 100-150 words, "
        "but you can go with more if needed. If the user specifies that it should be a long response, "
        "then feel free to disregard the response length restriction entirely.\n"
        "prompt:\n"
        f"{params.prompt_text}"
    )
    return context_prompt


@activity.defn
async def backfill_slack_user_info_activity() -> list[SlackUserCreate]:
    """
    Backfill slack user info.
    """

    slack_client = get_slack_web_client()
    slack_client.team_info()
    slack_user_team_pairs = get_user_teams_from_messages(
        slack_team_slack_id=slack_client.team_id
    )
    slack_user_creates = []
    for slack_user_slack_id, slack_team_slack_id in slack_user_team_pairs:
        try:
            slack_user_profile_response = slack_client.users_profile_get(
                user=slack_user_slack_id
            )
            if slack_user_profile_response.status_code != 200:
                raise RuntimeError(f"status not 200 {slack_user_profile_response}")
            slack_user_profile = slack_user_profile_response.get("profile")
            slack_user_creates.append(
                SlackUserCreate(
                    slack_id=slack_user_slack_id,
                    name=slack_user_profile.get("display_name")
                    or slack_user_profile.get("real_name"),
                    slack_team_slack_id=slack_team_slack_id,
                )
            )
        except Exception as e:
            logger.exception(e)

    # TODO - persist these some other way to avoid passing back via temporal?
    # maybe not so bad for my purposes, but definitely not scalable
    return slack_user_creates
