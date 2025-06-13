from unittest.mock import AsyncMock, Mock

import alembic.config
import pytest
from sqlalchemy import Engine
from sqlmodel import Session


@pytest.fixture
def mock_engine() -> Mock:
    """Provides a mock SQLAlchemy Engine."""
    return Mock(spec=Engine)


@pytest.fixture
def mock_session() -> Mock:
    """Provides a mock SQLModel Session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_alembic_config() -> Mock:
    """Provides a mock Alembic Config."""
    config = Mock(spec=alembic.config.Config)
    config.attributes = {}  # Common setup for alembic tests
    return config


# Temporal Workflow Testing Fixtures
@pytest.fixture
def mock_temporal_workflow():
    """Provides a mock temporal workflow for testing workflow.execute_activity calls."""
    mock_workflow = Mock()
    mock_workflow.execute_activity = AsyncMock()
    mock_workflow.start_activity = Mock()
    return mock_workflow


# AI Activity Mocks
@pytest.fixture
def mock_generate_gemini_response():
    """Mock for generate_gemini_response activity."""
    return AsyncMock(return_value="Generated AI response")


@pytest.fixture
def mock_generate_summary():
    """Mock for generate_summary activity."""
    return AsyncMock(return_value="Summary of previous conversations")


@pytest.fixture
def mock_get_vibe():
    """Mock for get_vibe activity."""
    return AsyncMock(return_value="Friendly and helpful")


@pytest.fixture
def mock_detect_call_to_action():
    """Mock for detect_call_to_action activity."""
    return AsyncMock(return_value=False)


# Slack Activity Mocks
@pytest.fixture
def mock_get_slack_channel_context():
    """Mock for get_slack_channel_context activity."""
    return AsyncMock(return_value=[])


@pytest.fixture
def mock_generate_context_prompt():
    """Mock for generate_context_prompt activity."""
    return AsyncMock(return_value="Context prompt for AI")


@pytest.fixture
def mock_fix_slack_tagging_activity():
    """Mock for fix_slack_tagging_activity."""
    return AsyncMock(return_value="Fixed slack message")


@pytest.fixture
def mock_backfill_slack_user_info_activity():
    """Mock for backfill_slack_user_info_activity."""
    return AsyncMock(return_value=[])


# DB Job Activity Mocks
@pytest.fixture
def mock_backfill_slack_messages_slack_user_id_activity():
    """Mock for backfill_slack_messages_slack_user_id_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_backfill_slack_messages_slack_channel_id_activity():
    """Mock for backfill_slack_messages_slack_channel_id_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_backfill_slack_messages_slack_team_id_activity():
    """Mock for backfill_slack_messages_slack_team_id_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_backfill_teams_from_messages_activity():
    """Mock for backfill_teams_from_messages_activity."""
    return AsyncMock(return_value=None)


@pytest.fixture
def mock_delete_slack_message_duplicates_activity():
    """Mock for delete_slack_message_duplicates_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_upsert_slack_user_creates_activity():
    """Mock for upsert_slack_user_creates_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_backfill_genai_text_slack_user_id_activity():
    """Mock for backfill_genai_text_slack_user_id_activity."""
    return AsyncMock(return_value="OK")


@pytest.fixture
def mock_backfill_genai_text_slack_channel_id_activity():
    """Mock for backfill_genai_text_slack_channel_id_activity."""
    return AsyncMock(return_value="OK")


# Sample Activity Mocks
@pytest.fixture
def mock_say_hello():
    """Mock for say_hello activity."""
    return AsyncMock(return_value="Formatted hello message")


@pytest.fixture
def mock_build_hello_prompt():
    """Mock for build_hello_prompt activity."""
    return AsyncMock(return_value="Say hello to test user in a friendly way.")
