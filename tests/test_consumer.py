"""
Tests for the consumer service, specifically testing data processing and Pub/Sub consumption.

This module tests the `process_data` and `pubsub_consumer` functions to ensure
correct calculations and data storage in the SQLite test database.
"""

import json
import base64
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import ProcessedData, Base
from app.schema import DataPayload
from app.consumer import process_data, pubsub_consumer, get_db
import pytz

# Define a separate test database URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# Configure the test engine and session
engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


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
    db = next(get_db(TEST_DATABASE_URL))
    try:
        # Execute the process_data function
        process_data(data_payload, db)

        # Query the database to verify the data insertion
        result = db.query(ProcessedData).first()

        # Validate calculated mean and standard deviation values
        expected_mean = 1.3853
        expected_stddev = 0.9215
        assert result.mean == pytest.approx(expected_mean, 0.001)
        assert result.stddev == pytest.approx(expected_stddev, 0.001)

        # Validate the UTC timestamp conversion
        expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
        assert result.utc_timestamp.replace(
            tzinfo=pytz.utc) == expected_utc_timestamp
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
    db = next(get_db(TEST_DATABASE_URL))
    try:
        # Invoke the consumer function
        pubsub_consumer(event, None)

        # Validate data stored in the test database
        result = db.query(ProcessedData).first()
        expected_mean = 1.3853
        expected_stddev = 0.9215

        assert result.mean == pytest.approx(expected_mean, 0.001)
        assert result.stddev == pytest.approx(expected_stddev, 0.001)

        # Validate the UTC timestamp conversion
        expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
        assert result.utc_timestamp.replace(
            tzinfo=pytz.utc) == expected_utc_timestamp
    finally:
        db.close()
