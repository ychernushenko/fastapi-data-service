"""
Consumer service for processing messages from Pub/Sub and saving processed data to the database.

This module listens to a Google Pub/Sub topic, processes the received data,
and stores the processed results in the database.
"""

import os
import json
import base64
import statistics
from datetime import datetime
import pytz
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from google.cloud.sql.connector import Connector
from .models import ProcessedData, Base
from .schema import DataPayload

# Initialize the Cloud SQL Connector
connector = Connector()

# Production database configuration from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_HOST = os.getenv("DB_HOST")  # This should be the instance connection name
CLOUD_SQL_DATABASE_URL = f"postgresql+pg8000://"


def get_db(database_url: str = CLOUD_SQL_DATABASE_URL):
    """
    Provides a database session for the specified database URL.

    If the database URL is the default (Cloud SQL), it connects using the Google Cloud SQL Connector
    to securely connect to the Cloud SQL instance. For testing, an SQLite database URL can be provided
    to run tests without connecting to Cloud SQL.

    Parameters:
        database_url (str): The database URL to connect to.

    Yields:
        sqlalchemy.orm.Session: A session bound to the specified database.
    """
    if "sqlite" in database_url:
        # Use SQLite for testing
        engine = create_engine(database_url, connect_args={
                               "check_same_thread": False})
    else:
        # Use Cloud SQL Connector for production
        def getconn():
            return connector.connect(
                DB_HOST,  # Instance connection name
                "pg8000",  # Use the pg8000 driver for PostgreSQL
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
            )
        engine = create_engine(CLOUD_SQL_DATABASE_URL, creator=getconn)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)  # Create tables if they don't exist

    db = SessionLocal()  # Create a new session
    try:
        yield db
    finally:
        db.close()


def process_data(data_payload: DataPayload, db_session: Session):
    """
    Processes a data payload by calculating the mean and standard deviation,
    then stores the results in the database.

    Parameters:
        data_payload (DataPayload): The data payload object to process.
        db_session (Session): The database session used to add and commit data.

    Raises:
        ValueError: If the data list in data_payload is empty or invalid.
    """
    # Parse the timestamp and convert to UTC
    utc_timestamp = datetime.strptime(
        data_payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z"
    ).astimezone(pytz.utc)

    # Calculate mean and standard deviation for the data
    mean_value = statistics.mean(data_payload.data)
    stddev_value = statistics.stdev(data_payload.data)

    # Create a new ProcessedData entry
    new_data = ProcessedData(
        utc_timestamp=utc_timestamp, mean=mean_value, stddev=stddev_value
    )
    db_session.add(new_data)
    db_session.commit()
    db_session.refresh(new_data)  # Refresh to get the updated instance


def pubsub_consumer(event, context, db_session=None):
    """
    Google Cloud Function entry point for processing Pub/Sub messages.

    This function decodes the base64-encoded Pub/Sub message payload, parses it into
    a DataPayload object, and processes the data by calculating statistical metrics,
    which are then stored in the database.

    Parameters:
        event (dict): The Pub/Sub message payload in base64 encoding.
        context (google.cloud.functions.Context): Metadata for the event.
        db_session (Session, optional): Optional database session for dependency injection.

    Raises:
        ValueError: If the message data is not properly formatted or fails to parse.
    """
    if db_session is None:
        # Get a new database session if none is provided
        db_session = next(get_db())

    # Decode and parse the Pub/Sub message
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data_payload = DataPayload(**json.loads(pubsub_message))

    # Process the data and store in the database
    process_data(data_payload, db_session)
