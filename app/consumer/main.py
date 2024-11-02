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
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.models import ProcessedData, Base
from app.schema import DataPayload
import pytz

# Production database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "appdb")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_db(database_url: str = DATABASE_URL):
    """
    Provides a database session for the specified database URL.

    Parameters:
        database_url (str): Database URL to connect to. Defaults to production DATABASE_URL.

    Yields:
        sqlalchemy.orm.Session: A session bound to the specified database.
    """
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def process_data(data_payload: DataPayload, db_session: Session):
    """
    Processes a data payload by calculating mean and standard deviation,
    then stores the results in the database.

    Parameters:
        data_payload (DataPayload): The data payload to process.
        db_session (Session): The database session used to add and commit data.
    """
    utc_timestamp = datetime.strptime(
        data_payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.utc)
    mean_value = statistics.mean(data_payload.data)
    stddev_value = statistics.stdev(data_payload.data)
    new_data = ProcessedData(
        utc_timestamp=utc_timestamp, mean=mean_value, stddev=stddev_value)
    db_session.add(new_data)
    db_session.commit()
    db_session.refresh(new_data)


def pubsub_consumer(event, context, db_session=None):
    """
    Google Cloud Function entry point for processing Pub/Sub messages.

    Parameters:
        event (dict): The Pub/Sub message payload in base64 encoding.
        context (google.cloud.functions.Context): Metadata for the event.
        db_session (Session, optional): Optional database session for dependency injection.
    """
    if db_session is None:
        db_session = next(get_db())
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    data_payload = DataPayload(**json.loads(pubsub_message))
    process_data(data_payload, db_session)
