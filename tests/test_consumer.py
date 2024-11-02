"""
Tests for the consumer processing logic in the data processing service.

Verifies the processing of data payloads, including mean and standard deviation calculations
and database storage.
"""

# test_consumer.py

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.consumer import process_data
from app.schema import DataPayload
from app.models import ProcessedData, Base
from datetime import datetime
import pytz

# Setup in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the in-memory database
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    session = SessionLocal()
    yield session
    session.close()


@patch("app.consumer.get_subscriber_client")
def test_process_data_calculations(mock_get_subscriber_client, db_session):
    """
    Tests the process_data function to ensure correct calculation of mean,
    standard deviation, and storage in the database.

    Verifies:
        - Correct values for mean and standard deviation.
        - Proper structure and field values in the `ProcessedData` record.
    """
    mock_get_subscriber_client.return_value = None  # Ensure pull_messages does not actually run

    # Define a sample data payload with known values
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",
        data=[0.379, 1.589, 2.188]
    )

    # Execute the processing function with the in-memory SQLite session
    process_data(data_payload, db_session)

    # Query the database to verify data was correctly inserted
    result = db_session.query(ProcessedData).first()

    # Validate mean and standard deviation values
    expected_mean = 1.3853
    expected_stddev = 0.9215
    assert result.mean == pytest.approx(expected_mean, 0.001)
    assert result.stddev == pytest.approx(expected_stddev, 0.001)

    # Validate the UTC timestamp
    expected_utc_timestamp = datetime(
        2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert result.utc_timestamp == expected_utc_timestamp
