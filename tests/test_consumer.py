import json
import pytest
from unittest.mock import patch
from datetime import datetime
from app.consumer import process_data, pubsub_consumer, get_db
from app.schema import DataPayload
from app.models import ProcessedData
import pytz
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Use a test database URL for testing
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="module")
def db_session():
    """
    Fixture to set up a database session for testing, using a test SQLite database.

    Yields:
        sqlalchemy.orm.Session: Database session for the test database.
    """
    # Create an engine using the test database
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    # Provide a session for the test
    db = TestingSessionLocal()
    yield db
    db.close()


def test_process_data(db_session):
    """
    Test process_data function to ensure correct calculations and data storage.
    """
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",
        data=[0.379, 1.589, 2.188]
    )

    process_data(data_payload, db_session)

    # Validate data stored in the test database
    result = db_session.query(ProcessedData).first()
    expected_mean = 1.3853
    expected_stddev = 0.9215

    assert result.mean == pytest.approx(expected_mean, 0.001)
    assert result.stddev == pytest.approx(expected_stddev, 0.001)

    expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert result.utc_timestamp == expected_utc_timestamp


def test_pubsub_consumer(db_session):
    """
    Test pubsub_consumer function by simulating a Pub/Sub event.
    """
    event = {
        'data': base64.b64encode(json.dumps({
            "time_stamp": "2019-05-01T06:00:00-04:00",
            "data": [0.379, 1.589, 2.188]
        }).encode('utf-8'))
    }

    with patch("app.consumer.get_db", return_value=iter([db_session])):
        pubsub_consumer(event, None)

    # Check database insertion
    result = db_session.query(ProcessedData).first()
    expected_mean = 1.3853
    expected_stddev = 0.9215

    assert result.mean == pytest.approx(expected_mean, 0.001)
    assert result.stddev == pytest.approx(expected_stddev, 0.001)
    expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert result.utc_timestamp == expected_utc_timestamp
