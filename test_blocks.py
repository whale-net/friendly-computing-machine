#!/usr/bin/env python3
"""Test script to verify the slack blocks functionality."""

from src.friendly_computing_machine.bot.slack_models import (
    create_worker_status_blocks,
    render_blocks_to_text,
)


def test_blocks():
    """Test creating blocks and rendering them to text."""
    # Create worker status blocks
    blocks = create_worker_status_blocks(
        friendly_name="Test Worker",
        name="test-worker",
        id="worker-123",
        current_status="RUNNING",
    )

    print("Created blocks:")
    for i, block in enumerate(blocks):
        print(f"  Block {i}: {type(block).__name__}")

    # Render to text
    text_output = render_blocks_to_text(blocks)
    print(f"\nRendered text:\n{text_output}")

    # Show what would be stored in database
    print(f"\nText for database: '{text_output}'")


if __name__ == "__main__":
    test_blocks()
