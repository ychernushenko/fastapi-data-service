"""
Tests for FastAPI data processing service with GCS and Pub/Sub.

Tests the API endpoint to verify successful GCS upload and Pub/Sub message publishing.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@patch("app.main.storage.Client")  # Mocking storage.Client
@patch("app.main.pubsub_v1.PublisherClient")  # Mocking PublisherClient
def test_receive_data_success(mock_publisher_client, mock_storage_client):
    """
    Tests the /data endpoint to ensure data is saved to GCS and a message is
    published to Pub/Sub on a successful request.
    """
    # Mock Google Cloud Storage upload behavior
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_string.return_value = None

    # Mock Pub/Sub publish behavior
    mock_publisher_client.return_value.publish.return_value = None

    # Test API endpoint
    response = client.post("/data/", json={
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    })

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Data received successfully"
    mock_blob.upload_from_string.assert_called_once()
    mock_publisher_client.return_value.publish.assert_called_once()
