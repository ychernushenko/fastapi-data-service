"""
Consumer service for processing messages from Pub/Sub and saving processed data to the database.

This module listens to a Google Pub/Sub topic, processes the received data,
and stores the processed results in PostgreSQL or an SQLite database for testing.
"""

import os
import json
import statistics
from datetime import datetime
from google.cloud import pubsub_v1
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.models import ProcessedData, Base
from app.schema import DataPayload
from fastapi import FastAPI, Depends
import pytz
import threading
from contextlib import asynccontextmanager

# Database configuration for production
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "appdb")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine(database_url: str = DATABASE_URL):
    """
    Return a database engine.

    Parameters:
        database_url (str): Database URL to connect to, default is production database.

    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine connected to the specified database.
    """
    return create_engine(database_url)

# Dependency to provide a session for the database


def get_db():
    """
    Provide a database session for production environment.

    Yields:
        sqlalchemy.orm.Session: A session bound to the production database.
    """
    engine = get_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


project_id = os.getenv("PROJECT_ID")
subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "data-subscription")

app = FastAPI()


def get_subscriber_client():
    """
    Initialize and return the Google Pub/Sub subscriber client.

    Returns:
        pubsub_v1.SubscriberClient: Google Pub/Sub subscriber client.
    """
    return pubsub_v1.SubscriberClient()


def process_data(data_payload: DataPayload, db_session: Session):
    """
    Process a data payload by calculating mean and standard deviation,
    then store the results in the database.

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


def pull_messages(db_session_factory):
    """
    Continuously pull messages from Pub/Sub and process them.

    Parameters:
        db_session_factory: Callable that provides a new database session.
    """
    subscriber = get_subscriber_client()
    subscription_path = subscriber.subscription_path(
        project_id, subscription_id)
    while True:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 10})
        for received_message in response.received_messages:
            data_payload = DataPayload(
                **json.loads(received_message.message.data.decode("utf-8")))
            with db_session_factory() as db_session:
                process_data(data_payload, db_session)
            subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": [
                                   received_message.ack_id]})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to start and stop the Pub/Sub message pulling.

    Parameters:
        app (FastAPI): FastAPI application instance.
    """
    db_session_factory = get_db  # Use production session by default
    thread = threading.Thread(target=pull_messages, args=(db_session_factory,))
    thread.start()
    yield
    thread.join()

app = FastAPI(lifespan=lifespan)
