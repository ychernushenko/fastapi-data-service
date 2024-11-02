"""
Tests for the consumer processing logic in the data processing service.

Verifies the processing of data payloads, including mean and standard deviation calculations
and database storage.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.consumer import process_data
from app.schema import DataPayload
from datetime import datetime
import pytz


@patch("app.consumer.pull_messages")
def test_process_data_calculations(mock_pull_messages):
    """
    Tests the process_data function to ensure correct calculation of mean,
    standard deviation, and storage in the database.

    Verifies:
        - Correct values for mean and standard deviation.
        - Proper structure and field values in the `ProcessedData` record.
    """
    mock_pull_messages.return_value = None  # Ensure pull_messages does not actually run

    # Create a mock session
    mock_session = MagicMock()

    # Define a sample data payload with known values
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",
        data=[0.379, 1.589, 2.188]
    )

    # Execute the processing function with the mock session
    process_data(data_payload, mock_session)

    # Assertions to verify the database calls
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()

    # Validate the added record
    added_record = mock_session.add.call_args[0][0]
    expected_mean = 1.3853
    expected_stddev = 0.9215
    assert added_record.mean == pytest.approx(expected_mean, 0.001)
    assert added_record.stddev == pytest.approx(expected_stddev, 0.001)

    expected_utc_timestamp = datetime(
        2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert added_record.utc_timestamp == expected_utc_timestamp
