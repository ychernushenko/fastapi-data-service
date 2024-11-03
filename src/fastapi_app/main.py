"""
Main application file for FastAPI data processing service.

This module contains the FastAPI app setup and route definitions, and it publishes
data directly to Google Pub/Sub without storing it in Cloud Storage.
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import pubsub_v1
from .schema import DataPayload

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


def get_publisher_client():
    """Initialize and return the Google Pub/Sub publisher client."""
    return pubsub_v1.PublisherClient()


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
    Receives data payload and publishes it directly to Pub/Sub.

    Parameters:
        payload (DataPayload): Data received via POST, containing timestamp and data list.

    Returns:
        dict: A success message confirming message publication.
    """
    try:
        # Publish message to Pub/Sub
        publish_message_to_pubsub(payload)
        return {"message": "Data received and published successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
