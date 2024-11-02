"""
Consumer service for processing messages from Pub/Sub and saving processed
data to the database.

This module listens to a Google Pub/Sub topic, processes the received data,
and stores the processed results in PostgreSQL.
"""

import os
import json
import statistics
from datetime import datetime
from google.cloud import pubsub_v1
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.models import ProcessedData, Base  # Import Base to create tables
from app.schema import DataPayload
import pytz

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Google Pub/Sub configuration
project_id = os.getenv("PROJECT_ID")
subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "data-subscription")
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# Ensure tables are created
Base.metadata.create_all(bind=engine)


def process_data(data_payload: DataPayload):
    """
    Processes the payload data by calculating mean and standard deviation,
    then stores the results in the database.

    Parameters:
        data_payload (DataPayload): The data payload to process.
    """
    # Convert timestamp to UTC
    utc_timestamp = datetime.strptime(
        data_payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.utc)

    # Calculate mean and standard deviation
    mean_value = statistics.mean(data_payload.data)
    stddev_value = statistics.stdev(data_payload.data)

    # Store results in database
    db = SessionLocal()
    new_data = ProcessedData(
        utc_timestamp=utc_timestamp, mean=mean_value, stddev=stddev_value
    )
    db.add(new_data)
    db.commit()
    db.refresh(new_data)


def callback(message):
    """
    Callback function to process Pub/Sub messages.
    Decodes the message, processes the data, and acknowledges the message.

    Parameters:
        message: The Pub/Sub message to process.
    """
    data_payload = DataPayload(**json.loads(message.data.decode("utf-8")))
    process_data(data_payload)
    message.ack()


# Subscribe to the Pub/Sub topic
streaming_pull_future = subscriber.subscribe(
    subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}...")
