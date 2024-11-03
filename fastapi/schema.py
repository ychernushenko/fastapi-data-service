"""
Pydantic schemas for FastAPI data processing service.
"""

from pydantic import BaseModel
from typing import List


class DataPayload(BaseModel):
    """
    Schema for the payload received in the /data endpoint.

    Attributes:
        time_stamp (str): Timestamp of the data submission in ISO 8601 format.
        data (List[float]): List of data values.
    """
    time_stamp: str
    data: List[float]
