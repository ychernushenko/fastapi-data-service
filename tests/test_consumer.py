"""
Tests for the consumer processing logic in the data processing service.

Verifies the processing of data payloads, storage in the database, and
the correct structure of `ProcessedData`.
"""

import pytest
from unittest.mock import patch
from app.consumer import process_data
from app.schema import DataPayload
from app.models import ProcessedData
from datetime import datetime
import pytz


@patch("app.consumer.SessionLocal")  # Mocking the database session
@patch("app.consumer.pubsub_v1.SubscriberClient")  # Mocking SubscriberClient
def test_process_data(mock_pubsub_client, mock_db_session):
    """
    Tests the process_data function to ensure correct calculation of mean,
    standard deviation, database storage, and the structure of `ProcessedData`.

    Verifies:
        - Correct values for mean and standard deviation.
        - Correct data structure with all required fields in `ProcessedData`.
    """
    # Prepare mock database session and data payload
    mock_session = mock_db_session.return_value
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",  # US/Eastern time
        data=[0.379, 1.589, 2.188]
    )

    # Execute the processing logic
    process_data(data_payload)

    # Check if the record was added to the database
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Retrieve the added record to verify its structure and values
    added_record = mock_session.add.call_args[0][0]

    # Ensure the record is of type ProcessedData
    assert isinstance(added_record, ProcessedData)

    # Check the values of mean and standard deviation
    assert added_record.mean == pytest.approx(1.3853, 0.001)
    assert added_record.stddev == pytest.approx(0.9084, 0.001)

    # Verify timestamp conversion to UTC
    # Converted from US/Eastern to UTC
    expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert added_record.utc_timestamp == expected_utc_timestamp

    # Ensure all required fields in `ProcessedData` are present and correctly typed
    assert isinstance(added_record.id, int)
    assert isinstance(added_record.utc_timestamp, datetime)
    assert isinstance(added_record.mean, float)
    assert isinstance(added_record.stddev, float)
