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
import time

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

project_id = os.getenv("PROJECT_ID")
subscription_id = os.getenv("PUBSUB_SUBSCRIPTION", "data-subscription")

# Ensure tables are created
Base.metadata.create_all(bind=engine)


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
    db.close()  # Close session after use


def pull_messages():
    """Pulls messages from Pub/Sub and processes them."""
    subscriber = get_subscriber_client()
    subscription_path = subscriber.subscription_path(
        project_id, subscription_id)

    while True:
        response = subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": 10,  # Adjust the number as needed
            }
        )

        if not response.received_messages:
            print("No new messages. Waiting...")
            time.sleep(5)  # Wait before polling again
            continue

        for received_message in response.received_messages:
            print(f"Received message: {received_message.message.data}")
            data_payload = DataPayload(
                **json.loads(received_message.message.data.decode("utf-8")))
            process_data(data_payload)
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": [received_message.ack_id],
                }
            )
            print("Message processed and acknowledged.")


if __name__ == "__main__":
    print("Starting pull-based Pub/Sub consumer...")
    pull_messages()
