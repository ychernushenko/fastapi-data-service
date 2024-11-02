"""
Tests for the consumer processing logic in the data processing service.

This module verifies the processing of data payloads, including mean and
standard deviation calculations and database storage.
"""

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.consumer import process_data
from app.schema import DataPayload
from app.models import ProcessedData, Base
from datetime import datetime
import pytz

# Setup in-memory SQLite engine for testing


@pytest.fixture(scope="module")
def test_engine():
    """
    Creates an in-memory SQLite database engine for testing.

    Returns:
        Engine: An SQLAlchemy engine instance for in-memory SQLite database.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)  # Create tables in in-memory SQLite
    yield engine
    Base.metadata.drop_all(bind=engine)  # Clean up after tests


@pytest.fixture(scope="module")
def db_session(test_engine):
    """
    Provides a SQLAlchemy session connected to the in-memory SQLite database.

    Returns:
        Session: A session for interacting with the in-memory SQLite database.
    """
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine)
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
    mock_get_subscriber_client.return_value = None  # Avoid actual Pub/Sub calls

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
