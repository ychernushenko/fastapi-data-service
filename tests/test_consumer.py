"""
Tests for the consumer processing logic in the data processing service.

Verifies the processing of data payloads, including mean and standard deviation calculations
and database storage.
"""

import pytest
from unittest.mock import patch
from app.consumer import process_data
from app.schema import DataPayload
from app.models import ProcessedData
from datetime import datetime
import pytz


@patch("app.consumer.SessionLocal")  # Mocking the database session
def test_process_data_calculations(mock_db_session):
    """
    Tests the process_data function to ensure correct calculation of mean,
    standard deviation, and storage in the database.

    Verifies:
        - Correct values for mean and standard deviation.
        - Proper structure and field values in the `ProcessedData` record.
    """
    # Mock the database session
    mock_session = mock_db_session.return_value

    # Define a sample data payload with known values
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",  # Original time in US/Eastern
        data=[0.379, 1.589, 2.188]
    )

    # Execute the processing function
    process_data(data_payload)

    # Verify that the database `add` and `commit` methods were called
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Retrieve the added record to validate calculations and field values
    added_record = mock_session.add.call_args[0][0]

    # Check that the record is an instance of ProcessedData
    assert isinstance(added_record, ProcessedData)

    # Validate the mean and standard deviation values
    expected_mean = 1.3853  # Calculated mean
    expected_stddev = 0.9084  # Calculated standard deviation
    assert added_record.mean == pytest.approx(expected_mean, 0.001)
    assert added_record.stddev == pytest.approx(expected_stddev, 0.001)

    # Validate the UTC timestamp conversion
    expected_utc_timestamp = datetime(
        2019, 5, 1, 10, 0, tzinfo=pytz.utc)  # Converted to UTC
    assert added_record.utc_timestamp == expected_utc_timestamp

    # Verify all required fields are correctly typed
    assert isinstance(added_record.id, int)
    assert isinstance(added_record.utc_timestamp, datetime)
    assert isinstance(added_record.mean, float)
    assert isinstance(added_record.stddev, float)
