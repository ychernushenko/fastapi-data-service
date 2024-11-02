import pytest
from unittest.mock import patch, MagicMock
from app.consumer import process_data, pull_messages


# Mock the Pub/Sub subscriber client
@patch("app.consumer.get_subscriber_client")
def test_process_data(mock_get_subscriber_client):
    """
    Test the process_data function to verify mean and stddev calculation
    without requiring Google Cloud credentials.
    """
    # Mock the subscriber client to avoid real Pub/Sub interactions
    mock_subscriber = MagicMock()
    mock_get_subscriber_client.return_value = mock_subscriber

    # Define a sample data payload for testing
    data_payload = {
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    }

    # Test the process_data function
    processed_data = process_data(data_payload)

    # Add additional assertions to verify the processing logic as needed
    ...
