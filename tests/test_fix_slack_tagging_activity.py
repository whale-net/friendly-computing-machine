import re
import asyncio
import pytest


def fix_slack_tagging_core_logic(text: str) -> str:
    """
    Core logic from fix_slack_tagging_activity function for testing.
    This function replaces @here and @channel with their escaped versions.
    """
    # Replace @here and @channel with their escaped versions only if not already escaped
    text = re.sub(r"(?<!<)@here", "<!here>", text)
    text = re.sub(r"(?<!<)@channel", "<!channel>", text)
    
    return text


class TestFixSlackTaggingActivity:
    """Test cases for fix_slack_tagging_activity function."""
    
    def test_simple_here_replacement(self):
        """Test basic @here replacement."""
        input_text = "Hello @here, please check this!"
        expected = "Hello <!here>, please check this!"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_simple_channel_replacement(self):
        """Test basic @channel replacement."""
        input_text = "Hello @channel, important update!"
        expected = "Hello <!channel>, important update!"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_both_replacements(self):
        """Test both @here and @channel in same text."""
        input_text = "Hey @channel and @here, meeting time!"
        expected = "Hey <!channel> and <!here>, meeting time!"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_already_escaped_here_not_changed(self):
        """Test that already escaped @here is not double-escaped."""
        input_text = "Already escaped <!here> should stay the same"
        expected = "Already escaped <!here> should stay the same"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_already_escaped_channel_not_changed(self):
        """Test that already escaped @channel is not double-escaped."""
        input_text = "Already escaped <!channel> should stay the same"
        expected = "Already escaped <!channel> should stay the same"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_mixed_escaped_and_unescaped(self):
        """Test mix of escaped and unescaped tags."""
        input_text = "Mix: @here and <!channel> and @channel"
        expected = "Mix: <!here> and <!channel> and <!channel>"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_multiple_here_tags(self):
        """Test multiple @here tags in text."""
        input_text = "@here start @here middle @here end"
        expected = "<!here> start <!here> middle <!here> end"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_multiple_channel_tags(self):
        """Test multiple @channel tags in text."""
        input_text = "@channel start @channel middle @channel end"
        expected = "<!channel> start <!channel> middle <!channel> end"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_empty_string(self):
        """Test empty string input."""
        input_text = ""
        expected = ""
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_no_tags(self):
        """Test text with no tags to replace."""
        input_text = "This is just normal text without any tags"
        expected = "This is just normal text without any tags"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_at_symbol_not_here_or_channel(self):
        """Test that other @mentions are not affected."""
        input_text = "Hello @user123 and @everyone, also @here"
        expected = "Hello @user123 and @everyone, also <!here>"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_partial_matches_are_replaced(self):
        """Test that partial matches like '@hereafter' are replaced (current behavior)."""
        input_text = "@hereafter and @channels and @here"
        expected = "<!here>after and <!channel>s and <!here>"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    def test_case_sensitivity(self):
        """Test that replacements are case sensitive."""
        input_text = "@HERE @Channel @here @channel"
        expected = "@HERE @Channel <!here> <!channel>"
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected
    
    @pytest.mark.parametrize("input_text,expected", [
        ("@here", "<!here>"),
        ("@channel", "<!channel>"),
        ("<!here>", "<!here>"),
        ("<!channel>", "<!channel>"),
        ("@here @channel", "<!here> <!channel>"),
        ("test @here test", "test <!here> test"),
        ("test @channel test", "test <!channel> test"),
    ])
    def test_parametrized_replacements(self, input_text, expected):
        """Parametrized test for various input/output combinations."""
        result = fix_slack_tagging_core_logic(input_text)
        assert result == expected


# Note: The actual function `fix_slack_tagging_activity` is an async function 
# with @activity.defn decorator from temporalio. The tests above validate the
# core regex logic used in that function.