import pytest
from fastapi.testclient import TestClient
from app.main import app, get_db
from unittest.mock import MagicMock, patch
from app.models import ProcessedData

client = TestClient(app)

@pytest.fixture
def mock_db_session():
    # Mock the SessionLocal function itself
    with patch("app.main.SessionLocal") as MockSession:
        # Create a mock instance to represent the actual session instance
        mock_session_instance = MagicMock()
        
        # Define behavior for `add`, `commit`, and `refresh` to avoid errors in `receive_data`
        mock_session_instance.add.return_value = None
        mock_session_instance.commit.return_value = None
        mock_session_instance.refresh.return_value = None

        # Set up mock for `SessionLocal` to return the session instance
        MockSession.return_value = mock_session_instance
        
        # Patch `get_db` dependency to use the mock session
        app.dependency_overrides[get_db] = lambda: mock_session_instance
        
        # Yield the mock session instance to use in tests
        yield mock_session_instance

def test_receive_data(mock_db_session):
    # Perform the test request
    response = client.post("/data/", json={
        "time_stamp": "2019-05-01T06:00:00-04:00",
        "data": [0.379, 1.589, 2.188]
    })

    # Assertions for the response
    assert response.status_code == 200
    assert "Data processed successfully" in response.json()["message"]

    # Ensure `add` and `commit` were called on the mock session
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
