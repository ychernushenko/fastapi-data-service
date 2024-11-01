"""
Main application file for FastAPI data processing service.

This module contains the FastAPI app setup and route definitions.
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import ProcessedData, Base  # Import Base to create tables
from app.schema import DataPayload
from datetime import datetime
import statistics
import pytz

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

# Application instance
app = FastAPI()

def get_db():
    """
    Dependency function to provide a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/data/")
async def receive_data(payload: DataPayload, db: Session = Depends(get_db)):
    """
    Receives data payload, calculates mean and standard deviation, 
    and stores it in the database.
    
    Parameters:
        payload (DataPayload): Data received via POST, containing timestamp and data list.
        db (Session): SQLAlchemy session dependency.

    Returns:
        dict: A success message with the ID of the stored record.
    """
    try:
        utc_timestamp = datetime.strptime(payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.utc)
        mean_value = statistics.mean(payload.data)
        stddev_value = statistics.stdev(payload.data)
        new_data = ProcessedData(
            utc_timestamp=utc_timestamp, mean=mean_value, stddev=stddev_value
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)
        return {"message": "Data processed successfully", "id": new_data.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
