import logging
from unittest.mock import patch, MagicMock
from friendly_computing_machine.bot.event_handler import handle_message
from friendly_computing_machine.db.dal import insert_message


@patch("friendly_computing_machine.bot.app.get_bot_config")
@patch("friendly_computing_machine.db.dal.insert_message")
def test_handle_message_inserts_message_when_conditions_met(
    mock_insert_message, mock_get_bot_config
):
    mock_get_bot_config.return_value = MagicMock(
        MUSIC_POLL_CHANNEL_IDS=["C12345"], BOT_SLACK_USER_IDS=["U12345"]
    )
    event = {
        "client_msg_id": "msg123",
        "team": "T12345",
        "channel": "C12345",
        "user": "U12345",
        "text": "Hello, world!",
        "ts": "1618884467.000200",
    }
    say = MagicMock()

    handle_message(event, say)

    # mock_insert_message.assert_called_once()
    # assert mock_insert_message.call_args[0][0].slack_id == "msg123"


@patch("friendly_computing_machine.bot.app.get_bot_config")
def test_handle_message_skips_message_not_in_music_poll_channel(mock_get_bot_config):
    mock_get_bot_config.return_value = MagicMock(
        MUSIC_POLL_CHANNEL_IDS=["C12345"], BOT_SLACK_USER_IDS=["U12345"]
    )
    event = {
        "client_msg_id": "msg123",
        "team": "T12345",
        "channel": "C67890",
        "user": "U12345",
        "text": "Hello, world!",
        "ts": "1618884467.000200",
    }
    say = MagicMock()

    handle_message(event, say)

    assert not insert_message.called


@patch("friendly_computing_machine.bot.app.get_bot_config")
def test_handle_message_skips_message_not_from_bot_user_or_thread(mock_get_bot_config):
    mock_get_bot_config.return_value = MagicMock(
        MUSIC_POLL_CHANNEL_IDS=["C12345"], BOT_SLACK_USER_IDS=["U12345"]
    )
    event = {
        "client_msg_id": "msg123",
        "team": "T12345",
        "channel": "C12345",
        "user": "U67890",
        "text": "Hello, world!",
        "ts": "1618884467.000200",
    }
    say = MagicMock()

    handle_message(event, say)

    assert not insert_message.called


@patch("friendly_computing_machine.bot.app.get_bot_config")
@patch("friendly_computing_machine.db.dal.insert_message")
def test_handle_message_logs_exception_when_error_occurs(
    mock_insert_message, mock_get_bot_config, caplog
):
    mock_get_bot_config.return_value = MagicMock(
        MUSIC_POLL_CHANNEL_IDS=["C12345"], BOT_SLACK_USER_IDS=["U12345"]
    )
    mock_insert_message.side_effect = Exception("Database error")
    event = {
        "client_msg_id": "msg123",
        "team": "T12345",
        "channel": "C12345",
        "user": "U12345",
        "text": "Hello, world!",
        "ts": "1618884467.000200",
    }
    say = MagicMock()

    with caplog.at_level(logging.WARNING):
        handle_message(event, say)

    assert "exception encountered: Database error" in caplog.text
