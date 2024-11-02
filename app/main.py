"""
Main application file for FastAPI data processing service.

This module contains the FastAPI app setup, route definitions, and functions for 
saving data to Google Cloud Storage and publishing messages to Google Pub/Sub.
"""

import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage, pubsub_v1
from app.schema import DataPayload

bucket_name = os.getenv("BUCKET_NAME", "fastapi-data-service")
project_id = os.getenv("PROJECT_ID")
topic_id = os.getenv("PUBSUB_TOPIC", "data-topic")

# FastAPI application instance
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_storage_client():
    """Initialize and return the Google Cloud Storage client."""
    return storage.Client()


def get_publisher_client():
    """Initialize and return the Google Pub/Sub publisher client."""
    return pubsub_v1.PublisherClient()


def upload_to_gcs(data_payload: DataPayload) -> str:
    """
    Uploads the received data payload to Google Cloud Storage.

    Parameters:
        data_payload (DataPayload): Data received in the request.

    Returns:
        str: Path to the stored object in Google Cloud Storage.
    """
    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f"data/{datetime.now().isoformat()}.json")
    blob.upload_from_string(json.dumps(data_payload.dict()))
    return blob.name


def publish_message_to_pubsub(data_payload: DataPayload) -> None:
    """
    Publishes the payload data to a Google Pub/Sub topic.

    Parameters:
        data_payload (DataPayload): The payload to be published to Pub/Sub.
    """
    client = get_publisher_client()
    topic_path = client.topic_path(project_id, topic_id)
    message_json = json.dumps(data_payload.dict())
    message_bytes = message_json.encode("utf-8")
    client.publish(topic_path, data=message_bytes)


@app.post("/data/")
async def receive_data(payload: DataPayload):
    """
    Receives data payload, stores it in Google Cloud Storage, and publishes a
    message to Pub/Sub.

    Parameters:
        payload (DataPayload): Data received via POST, containing timestamp and data list.

    Returns:
        dict: A success message with the GCS path of the stored object.
    """
    try:
        # Save payload to GCS
        gcs_path = upload_to_gcs(payload)

        # Publish message to Pub/Sub
        publish_message_to_pubsub(payload)

        return {"message": "Data received successfully", "gcs_path": gcs_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
