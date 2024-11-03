"""
Tests for the Pub/Sub consumer and data processing functions in consumer/main.py.

These tests simulate Pub/Sub events and verify that data is correctly processed and stored
in a test SQLite database.
"""

import json
import base64
import pytest
from consumer.main import process_data, pubsub_consumer, get_db
from consumer.models import ProcessedData
from consumer.schema import DataPayload
from datetime import datetime
import pytz

# Set up a test database URL with SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


def test_process_data():
    """
    Test the process_data function to ensure correct calculations for mean,
    standard deviation, and data storage in the test database.
    """
    # Initialize the test database session using get_db
    db = next(get_db(TEST_DATABASE_URL))

    try:
        data_payload = DataPayload(
            time_stamp="2019-05-01T06:00:00-04:00",
            data=[0.379, 1.589, 2.188]
        )

        # Call process_data with the test session
        process_data(data_payload, db)

        # Query the database to verify data insertion
        result = db.query(ProcessedData).first()
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
        db.close()  # Ensure the session is closed after the test


def test_pubsub_consumer():
    """
    Test the pubsub_consumer function by simulating a Pub/Sub event.
    This test checks if the function correctly decodes, processes, and stores data in the database.
    """
    # Initialize the test database session using get_db
    db = next(get_db(TEST_DATABASE_URL))

    try:
        # Simulate Pub/Sub event with base64 encoded data
        event = {
            'data': base64.b64encode(json.dumps({
                "time_stamp": "2019-05-01T06:00:00-04:00",
                "data": [0.379, 1.589, 2.188]
            }).encode('utf-8'))
        }

        # Call pubsub_consumer with the test session
        pubsub_consumer(event, None, db_session=db)

        # Verify data was inserted in the database
        result = db.query(ProcessedData).first()
        assert result is not None
    finally:
        db.close()  # Ensure the session is closed after the test
