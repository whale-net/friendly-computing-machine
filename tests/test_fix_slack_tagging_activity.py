import asyncio
import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock ALL the dependencies that could cause import issues
modules_to_mock = [
    'typer',
    'alembic',
    'sqlalchemy',
    'sqlmodel',
    'psycopg2',
    'google.generativeai',
    'slack_bolt',
    'opentelemetry',
    'opentelemetry.api',
    'opentelemetry.distro',
    'opentelemetry.exporter.otlp',
    'opentelemetry.sdk',
    'friendly_computing_machine.bot.app',
    'friendly_computing_machine.db.dal',
    'friendly_computing_machine.models.genai',
    'friendly_computing_machine.models.slack',
    'friendly_computing_machine.cli.main',
    'friendly_computing_machine.cli.bot_cli',
    'friendly_computing_machine.cli.context.db',
]

for module in modules_to_mock:
    sys.modules[module] = MagicMock()

# Import the actual function
from friendly_computing_machine.temporal.slack.activity import fix_slack_tagging_activity


class TestFixSlackTaggingActivity:
    """Test cases for fix_slack_tagging_activity function."""
    
    @pytest.mark.asyncio
    async def test_simple_here_replacement(self):
        """Test basic @here replacement."""
        input_text = "Hello @here, please check this!"
        expected = "Hello <!here>, please check this!"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_simple_channel_replacement(self):
        """Test basic @channel replacement."""
        input_text = "Hello @channel, important update!"
        expected = "Hello <!channel>, important update!"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_both_replacements(self):
        """Test both @here and @channel in same text."""
        input_text = "Hey @channel and @here, meeting time!"
        expected = "Hey <!channel> and <!here>, meeting time!"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_already_escaped_here_not_changed(self):
        """Test that already escaped @here is not double-escaped."""
        input_text = "Already escaped <!here> should stay the same"
        expected = "Already escaped <!here> should stay the same"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_already_escaped_channel_not_changed(self):
        """Test that already escaped @channel is not double-escaped."""
        input_text = "Already escaped <!channel> should stay the same"
        expected = "Already escaped <!channel> should stay the same"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_mixed_escaped_and_unescaped(self):
        """Test mix of escaped and unescaped tags."""
        input_text = "Mix: @here and <!channel> and @channel"
        expected = "Mix: <!here> and <!channel> and <!channel>"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_multiple_here_tags(self):
        """Test multiple @here tags in text."""
        input_text = "@here start @here middle @here end"
        expected = "<!here> start <!here> middle <!here> end"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_multiple_channel_tags(self):
        """Test multiple @channel tags in text."""
        input_text = "@channel start @channel middle @channel end"
        expected = "<!channel> start <!channel> middle <!channel> end"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_empty_string(self):
        """Test empty string input."""
        input_text = ""
        expected = ""
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_no_tags(self):
        """Test text with no tags to replace."""
        input_text = "This is just normal text without any tags"
        expected = "This is just normal text without any tags"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_at_symbol_not_here_or_channel(self):
        """Test that other @mentions are not affected."""
        input_text = "Hello @user123 and @everyone, also @here"
        expected = "Hello @user123 and @everyone, also <!here>"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_partial_matches_are_replaced(self):
        """Test that partial matches like '@hereafter' are replaced (current behavior)."""
        input_text = "@hereafter and @channels and @here"
        expected = "<!here>after and <!channel>s and <!here>"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_case_sensitivity(self):
        """Test that replacements are case sensitive."""
        input_text = "@HERE @Channel @here @channel"
        expected = "@HERE @Channel <!here> <!channel>"
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("input_text,expected", [
        ("@here", "<!here>"),
        ("@channel", "<!channel>"),
        ("<!here>", "<!here>"),
        ("<!channel>", "<!channel>"),
        ("@here @channel", "<!here> <!channel>"),
        ("test @here test", "test <!here> test"),
        ("test @channel test", "test <!channel> test"),
    ])
    async def test_parametrized_replacements(self, input_text, expected):
        """Parametrized test for various input/output combinations."""
        result = await fix_slack_tagging_activity(input_text)
        assert result == expected