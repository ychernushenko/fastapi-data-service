"""
Tests for the FastAPI data processing service with Pub/Sub.

This module verifies the behavior of the /data endpoint, ensuring that
data is correctly published to Google Pub/Sub when a valid request is made.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from consumer import app
from shared.schema import DataPayload
import json

client = TestClient(app)


@patch("app.main.get_publisher_client")
def test_receive_data_success(mock_get_publisher_client):
    """
    Tests the /data endpoint to ensure data is published to Pub/Sub on a successful request.

    This test verifies that:
        - A POST request to /data with a valid payload publishes the data to Pub/Sub.
        - The response contains a success message and status code 200.
        - The Pub/Sub client’s publish method is called once with the correct data.

    Mocks:
        - `get_publisher_client`: Replaces the Pub/Sub client to avoid real Google Cloud interaction.
    """
    # Mock the publish method to simulate Pub/Sub behavior without actual Google Cloud interaction
    mock_publisher_client = MagicMock()
    mock_get_publisher_client.return_value = mock_publisher_client
    mock_publisher_client.publish.return_value = None

    # Define a sample payload for the test
    payload = {
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    }

    # Send a POST request to the /data endpoint
    response = client.post("/data/", json=payload)

    # Assertions to check the response and that publish was called
    assert response.status_code == 200
    assert response.json()[
        "message"] == "Data received and published successfully"
    mock_publisher_client.publish.assert_called_once()

    # Check that the published message matches the payload
    published_data = mock_publisher_client.publish.call_args[1]["data"]
    published_payload = DataPayload(
        **json.loads(published_data.decode("utf-8")))
    assert published_payload.time_stamp == payload["time_stamp"]
    assert published_payload.data == payload["data"]
