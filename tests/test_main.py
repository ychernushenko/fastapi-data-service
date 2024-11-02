from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@patch("app.main.get_storage_client")
@patch("app.main.get_publisher_client")
def test_receive_data_success(mock_publisher_client, mock_storage_client):
    """
    Tests the /data endpoint to ensure data is saved to GCS and a message is
    published to Pub/Sub on a successful request.
    """
    mock_bucket = mock_storage_client.return_value.bucket.return_value
    mock_blob = mock_bucket.blob.return_value
    mock_blob.upload_from_string.return_value = None
    mock_publisher_client.return_value.publish.return_value = None

    response = client.post("/data/", json={
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Data received successfully"
    mock_blob.upload_from_string.assert_called_once()
    mock_publisher_client.return_value.publish.assert_called_once()
