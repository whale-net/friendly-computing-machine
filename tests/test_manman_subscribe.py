"""
Basic tests for the ManMan Subscribe Service
"""

from unittest.mock import Mock

from friendly_computing_machine.bot.subscribe.service import ManManSubscribeService


def test_service_initialization():
    """Test that the service can be initialized with required parameters."""
    # Mock the RabbitMQ connection and Slack API
    mock_rabbitmq_connection = Mock()
    mock_slack_api = Mock()

    service = ManManSubscribeService(
        rabbitmq_connection=mock_rabbitmq_connection,
        slack_api=mock_slack_api,
    )

    assert service._rabbitmq_connection == mock_rabbitmq_connection
    assert service._slack_api == mock_slack_api
    assert not service._is_running
