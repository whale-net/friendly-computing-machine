"""Test suite for Slack model utilities."""

from friendly_computing_machine.bot.slack_models import (
    create_worker_status_blocks,
    render_blocks_to_text,
)


def test_create_and_render_worker_status_blocks():
    """Test creating worker status blocks and rendering them to text."""
    worker_name = "Test Worker"
    worker_id = "worker-123"
    # Create worker status blocks
    blocks = create_worker_status_blocks(
        friendly_name=worker_name,
        name="test-worker",
        id=worker_id,
        current_status="RUNNING",
    )

    assert blocks is not None
    assert len(blocks) > 0, "No blocks were created"

    # Render to text
    text_output = render_blocks_to_text(blocks)
    assert text_output is not None
    assert isinstance(text_output, str)
    assert len(text_output.strip()) > 0, "Rendered text is empty"
    assert worker_name in text_output
    assert worker_id in text_output
    assert "RUNNING" in text_output

    print(f"Rendered text for verification:\n{text_output}")
