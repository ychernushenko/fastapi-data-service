from pydantic import BaseModel
from typing import List

class DataPayload(BaseModel):
    time_stamp: str
    data: List[float]
