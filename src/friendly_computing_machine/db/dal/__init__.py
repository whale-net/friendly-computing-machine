"""DAL (Data Access Layer) module for database operations.

This module provides organized data access functions grouped by model.
All functions are exposed here for backward compatibility.
"""

# Import all functions from submodules for backward compatibility
from .genai_dal import (
    get_genai_text_by_id,
    get_genai_texts,
    get_genai_texts_by_slack_channel,
    insert_genai_text,
    update_genai_text_response,
)
from .manman_dal import (
    delete_manman_status_update,
    get_manman_status_update_by_id,
    get_manman_status_update_from_create,
    get_manman_status_updates,
    insert_manman_status_update,
    update_manman_status_update,
)
from .music_poll_dal import (
    delete_music_poll,
    delete_music_poll_instance,
    delete_music_poll_response,
    get_music_poll_by_id,
    get_music_poll_instance_by_id,
    get_music_poll_instances,
    get_music_poll_response_by_id,
    get_music_poll_responses,
    get_music_polls,
    get_recent_music_poll_instances,
    get_unprocessed_music_poll_instances,
    insert_music_poll,
    insert_music_poll_instance,
    insert_music_poll_response,
    insert_music_poll_responses,
    update_music_poll,
    update_music_poll_instance,
    update_music_poll_response,
)
from .slack_dal import (
    find_poll_instance_messages,
    get_bot_slack_user_slack_ids,
    get_music_poll_channel_slack_ids,
    get_slack_channel,
    get_slack_command_by_id,
    get_slack_team_id_map,
    get_slack_teams,
    get_user_teams_from_messages,
    insert_message,
    insert_slack_command,
    select_distinct_slack_team_slack_id_from_slack_message,
    update_slack_command,
    upsert_message,
    upsert_slack_team,
    upsert_slack_teams,
    upsert_slack_users,
    upsert_slack_users_activity,
)
from .task_dal import (
    get_last_successful_task_instance,
    insert_task_instances,
    upsert_task,
    upsert_tasks,
)

__all__ = [
    # Slack functions
    "get_music_poll_channel_slack_ids",
    "get_bot_slack_user_slack_ids",
    "insert_message",
    "upsert_message",
    "select_distinct_slack_team_slack_id_from_slack_message",
    "upsert_slack_teams",
    "upsert_slack_team",
    "get_slack_teams",
    "get_slack_team_id_map",
    "get_user_teams_from_messages",
    "upsert_slack_users",
    "upsert_slack_users_activity",
    "get_slack_channel",
    "find_poll_instance_messages",
    "insert_slack_command",
    "get_slack_command_by_id",
    "update_slack_command",
    # Task functions
    "upsert_tasks",
    "upsert_task",
    "insert_task_instances",
    "get_last_successful_task_instance",
    # GenAI functions
    "insert_genai_text",
    "get_genai_texts",
    "get_genai_texts_by_slack_channel",
    "get_genai_text_by_id",
    "update_genai_text_response",
    # Music Poll functions
    "insert_music_poll",
    "get_music_poll_by_id",
    "get_music_polls",
    "update_music_poll",
    "delete_music_poll",
    "insert_music_poll_instance",
    "get_music_poll_instance_by_id",
    "get_music_poll_instances",
    "get_unprocessed_music_poll_instances",
    "get_recent_music_poll_instances",
    "update_music_poll_instance",
    "delete_music_poll_instance",
    "insert_music_poll_responses",
    "insert_music_poll_response",
    "get_music_poll_response_by_id",
    "get_music_poll_responses",
    "update_music_poll_response",
    "delete_music_poll_response",
    # ManMan functions
    "insert_manman_status_update",
    "get_manman_status_update_by_id",
    "get_manman_status_updates",
    "update_manman_status_update",
    "delete_manman_status_update",
    "get_manman_status_update_from_create",
]
