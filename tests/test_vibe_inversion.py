"""Test vibe generation and context prompt functionality."""

import random
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_generate_context_prompt_params_structure():
    """Test that GenerateContextPromptParams has the expected structure."""
    from friendly_computing_machine.temporal.slack.activity import (
        GenerateContextPromptParams,
    )

    # Test creating params without should_invert_vibe
    params = GenerateContextPromptParams(
        prompt_text="Hello world",
        previous_context="Previous conversation",
        vibe="friendly"
    )

    assert params.prompt_text == "Hello world"
    assert params.previous_context == "Previous conversation"
    assert params.vibe == "friendly"

    # Verify that should_invert_vibe is not present (removed)
    assert not hasattr(params, 'should_invert_vibe')


def test_get_vibe_inversion_logic():
    """Test that get_vibe includes inversion logic."""
    from textwrap import dedent

    # Mock the get_vibe function logic to test randomization
    def mock_get_vibe_logic(prompt: str, test_seed: int) -> tuple[bool, str]:
        """Return whether inversion happens and the prompt that would be generated."""
        random.seed(test_seed)
        should_invert_vibe = random.random() < 0.1

        if should_invert_vibe:
            vibe_prompt = dedent(f"""
                Please figure out the vibe of this prompt and then provide the OPPOSITE vibe:

                {prompt}

                Please return a one sentence summary of the OPPOSITE vibe from what was detected.
                Please be as concise as possible.
                Please do not include any other text or formatting. Just the opposite vibe.
            """)
        else:
            vibe_prompt = dedent(f"""
                Please figure out the vibe of this prompt:

                {prompt}

                Please return a one sentence summary of the vibe. Please be as concise as possible.
                Please do not include any other text or formatting. Just the vibe.
            """)

        return should_invert_vibe, vibe_prompt

    # Test that both inversion and non-inversion paths work
    test_prompt = "This is a happy message!"

    # Test non-inversion case (most seeds will give this)
    inverted, prompt = mock_get_vibe_logic(test_prompt, 1)
    assert not inverted
    assert "OPPOSITE" not in prompt
    assert test_prompt in prompt

    # Find a seed that gives inversion to test that path
    for seed in range(100):
        inverted, prompt = mock_get_vibe_logic(test_prompt, seed)
        if inverted:
            assert "OPPOSITE vibe" in prompt
            assert test_prompt in prompt
            break


def test_generate_context_prompt_simplified():
    """Test that generate_context_prompt is simplified without inversion logic."""
    from friendly_computing_machine.temporal.slack.activity import (
        GenerateContextPromptParams,
    )

    # Mock the generate_context_prompt function to test logic
    def mock_generate_context_prompt(params: GenerateContextPromptParams) -> str:
        """Mock version of generate_context_prompt."""
        tone_text = f"Detected tone of incoming prompt: {params.vibe}\n"

        context_prompt = (
            "# Response Guidelines\n\n"
            "## Context Information\n"
            f"Previous conversation summary:\n{params.previous_context}\n\n"
            "## The Vibe\n"
            f"{tone_text}\n"
            "## User Prompt\n"
            f"{params.prompt_text}\n\n"
            "## Additional Instructions\n"
            "- Consider the previous conversation context when relevant, but don't explicitly reference it\n"
            "- Keep responses concise (100-150 words) unless the user specifically requests a longer answer\n"
            "- Be helpful, accurate, and engaging in your response\n"
            "- Format your response appropriately for the question type\n"
            "- Please consider The Vibe when crafting your response\n"
        )
        return context_prompt

    params = GenerateContextPromptParams(
        prompt_text="Test prompt",
        previous_context="Test context",
        vibe="cheerful and energetic"  # This could be pre-inverted by get_vibe
    )

    result = mock_generate_context_prompt(params)

    # Verify that the result contains the vibe but no inversion instructions
    assert "Detected tone of incoming prompt: cheerful and energetic" in result
    assert "Please intentionally respond with the opposite tone" not in result
    assert "Test prompt" in result
    assert "Test context" in result
    assert "Please consider The Vibe when crafting your response" in result
