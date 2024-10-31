import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base,sessionmaker, Session
from app.models import ProcessedData
from app.schema import DataPayload
from datetime import datetime
import statistics
import pytz

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Application instance
app = FastAPI()

# Dependency to get the database session
def get_db():
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
    """
    try:
        # Debug: Check payload structure
        print("Received payload:", payload)

        # Convert timestamp to UTC without re-localizing
        utc_timestamp = datetime.strptime(payload.time_stamp, "%Y-%m-%dT%H:%M:%S%z").astimezone(pytz.utc)

        # Debug: Check converted timestamp
        print("Converted UTC timestamp:", utc_timestamp)

        # Calculate statistics
        mean_value = statistics.mean(payload.data)
        stddev_value = statistics.stdev(payload.data)

        # Debug: Check calculated statistics
        print("Mean:", mean_value, "Standard Deviation:", stddev_value)

        # Store data in the database
        new_data = ProcessedData(
            utc_timestamp=utc_timestamp, mean=mean_value, stddev=stddev_value
        )
        db.add(new_data)
        db.commit()
        db.refresh(new_data)

        return {"message": "Data processed successfully", "id": new_data.id}
    except Exception as e:
        # Debug: Log exception details
        print("Exception occurred:", e)
        raise HTTPException(status_code=400, detail=str(e))