import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.consumer import process_data
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


@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to provide a clean database session for each test.

    Yields:
        Session: SQLAlchemy session for interacting with the test database.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_process_data_calculations(db_session):
    """
    Test the process_data function to ensure correct calculations for mean,
    standard deviation, and data storage in the test database.

    Parameters:
        db_session (Session): Database session provided by the fixture.
    """
    data_payload = DataPayload(
        time_stamp="2019-05-01T06:00:00-04:00",
        data=[0.379, 1.589, 2.188]
    )

    # Execute the process_data function with the test session
    process_data(data_payload, db_session)

    # Query the database to verify the data insertion
    result = db_session.query(ProcessedData).first()

    # Validate calculated mean and standard deviation values
    expected_mean = 1.3853
    expected_stddev = 0.9215
    assert result.mean == pytest.approx(expected_mean, 0.001)
    assert result.stddev == pytest.approx(expected_stddev, 0.001)

    # Validate the UTC timestamp conversion
    expected_utc_timestamp = datetime(2019, 5, 1, 10, 0, tzinfo=pytz.utc)
    assert result.utc_timestamp == expected_utc_timestamp
