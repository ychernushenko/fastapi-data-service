"""
Database models for FastAPI data processing service.
"""

from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ProcessedData(Base):
    """
    SQLAlchemy model for storing processed data.

    Attributes:
        id (int): Primary key identifier.
        utc_timestamp (datetime): UTC timestamp of the data record.
        mean (float): Mean of the data values.
        stddev (float): Standard deviation of the data values.
    """
    __tablename__ = "processed_data"
    id = Column(Integer, primary_key=True, index=True)
    utc_timestamp = Column(DateTime, index=True)
    mean = Column(Float)
    stddev = Column(Float)
