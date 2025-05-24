"""
Basic tests for the ManMan Subscribe Service
"""

from friendly_computing_machine.bot.subscribe.service import ManManSubscribeService


def test_service_initialization():
    """Test that the service can be initialized with required parameters."""
    service = ManManSubscribeService(
        rabbitmq_url="amqp://test:test@localhost:5672/",
        slack_bot_token="xoxb-test-token",
    )

    assert service.rabbitmq_url == "amqp://test:test@localhost:5672/"
    assert service.slack_bot_token == "xoxb-test-token"
    assert not service._running
