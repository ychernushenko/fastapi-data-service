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
from fastapi import FastAPI
import pytz
import time
import threading

# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "appdb")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

project_id = os.getenv("PROJECT_ID")
subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "data-subscription")

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_subscriber_client():
    """Initialize and return the Google Pub/Sub subscriber client."""
    return pubsub_v1.SubscriberClient()


def process_data(data_payload: DataPayload):
    """
    Processes the payload data by calculating mean and standard deviation,
    then stores the results in the database.

    Parameters:
        data_payload (DataPayload): The data payload to process.
    """
    utc_timestamp = datetime.strptime(
        data_payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.utc)
    mean_value = statistics.mean(data_payload.data)
    stddev_value = statistics.stdev(data_payload.data)

    db = SessionLocal()
    new_data = ProcessedData(utc_timestamp=utc_timestamp,
                             mean=mean_value, stddev=stddev_value)
    db.add(new_data)
    db.commit()
    db.refresh(new_data)
    db.close()


def pull_messages():
    """Pulls messages from Pub/Sub and processes them."""
    subscriber = get_subscriber_client()
    subscription_path = subscriber.subscription_path(
        project_id, subscription_id)

    while True:
        response = subscriber.pull(
            request={"subscription": subscription_path, "max_messages": 10})

        for received_message in response.received_messages:
            data_payload = DataPayload(
                **json.loads(received_message.message.data.decode("utf-8")))
            process_data(data_payload)
            subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": [
                                   received_message.ack_id]})

        time.sleep(5)


@app.on_event("startup")
def startup_event():
    """Starts pulling messages in a background thread when the service starts."""
    thread = threading.Thread(target=pull_messages)
    thread.start()
