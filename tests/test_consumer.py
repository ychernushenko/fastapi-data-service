from unittest.mock import patch, MagicMock
from app.consumer import start_subscriber


@patch("app.consumer.get_subscriber_client")
def test_start_subscriber(mock_subscriber_client):
    """
    Tests the start_subscriber function to ensure it initializes the subscriber
    and begins listening to messages without triggering Google Cloud credentials.
    """
    mock_subscriber_client.return_value.subscribe.return_value = MagicMock()
    start_subscriber()
    mock_subscriber_client.return_value.subscribe.assert_called_once()
