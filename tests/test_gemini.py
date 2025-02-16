from unittest.mock import patch, MagicMock
from friendly_computing_machine.gemini.ai import generate_text_with_slack_context


@patch("ai.get_genai_texts_by_slack_channel")
@patch("ai.generate_text")
def test_generate_text_with_slack_context_generates_correct_text(
    mock_generate_text, mock_get_genai_texts
):
    mock_get_genai_texts.return_value = [
        MagicMock(prompt="Previous prompt 1", response="Previous response 1"),
        MagicMock(prompt="Previous prompt 2", response="Previous response 2"),
    ]
    mock_generate_text.side_effect = [
        ("Summarized topics", None),
        ("Generated response", None),
    ]

    result = generate_text_with_slack_context("user", "New prompt", "channel_id")

    assert result == ("Generated response", None)


@patch("ai.get_genai_texts_by_slack_channel")
@patch("ai.generate_text")
def test_generate_text_with_slack_context_handles_empty_previous_messages(
    mock_generate_text, mock_get_genai_texts
):
    mock_get_genai_texts.return_value = []
    mock_generate_text.side_effect = [
        ("Summarized topics", None),
        ("Generated response", None),
    ]

    result = generate_text_with_slack_context("user", "New prompt", "channel_id")

    assert result == ("Generated response", None)
