"""
Tests for FastAPI data processing service with GCS and Pub/Sub.

Tests the API endpoint to verify successful GCS upload and Pub/Sub message publishing.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@patch("app.main.upload_to_gcs")
@patch("app.main.publish_message_to_pubsub")
def test_receive_data_success(mock_publish, mock_upload):
    """
    Tests the /data endpoint to ensure data is saved to GCS and a message is
    published to Pub/Sub on a successful request.
    """
    mock_upload.return_value = "data/test.json"
    response = client.post("/data/", json={
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Data received successfully"
    mock_upload.assert_called_once()
    mock_publish.assert_called_once()
