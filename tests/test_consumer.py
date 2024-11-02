import json
import base64
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.consumer import process_data, pubsub_consumer
from app.models import ProcessedData, Base
from app.schema import DataPayload
from datetime import datetime
import pytz

# Define a separate test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    """
    Provide a database session for testing with the test database URL.

    Yields:
        sqlalchemy.orm.Session: A session bound to the test database.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_process_data():
    """
    Test the process_data function to ensure correct calculations for mean,
    standard deviation, and data storage in the test database.
    """
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",
        data=[0.379, 1.589, 2.188]
    )

    # Use the test database session directly
    db = next(override_get_db())
    try:
        process_data(data_payload, db)

        # Query the database to verify the data insertion
        result = db.query(ProcessedData).first()

        # Validate calculated mean and standard deviation values
        expected_mean = 1.3853
        expected_stddev = 0.9215
        assert result.mean == pytest.approx(expected_mean, 0.001)
        assert result.stddev == pytest.approx(expected_stddev, 0.001)

        # Validate the UTC timestamp conversion, ignoring timezone info
        expected_utc_timestamp = datetime(
            2019, 5, 1, 10, 0, tzinfo=pytz.utc).replace(tzinfo=None)
        assert result.utc_timestamp.replace(
            tzinfo=None) == expected_utc_timestamp
    finally:
        db.close()


def test_pubsub_consumer():
    """
    Test pubsub_consumer function by simulating a Pub/Sub event.

    This test checks if the function correctly decodes, processes, and
    stores data in the database.
    """
    # Simulate Pub/Sub event with base64 encoded data
    event = {
        'data': base64.b64encode(json.dumps({
            "time_stamp": "2019-05-01T06:00:00-04:00",
            "data": [0.379, 1.589, 2.188]
        }).encode('utf-8'))
    }

    # Use the test database session directly
    db = next(override_get_db())
    try:
        pubsub_consumer(event, None)

        # Query the database to verify data insertion
        result = db.query(ProcessedData).first()
        assert result is not None
    finally:
        db.close()
