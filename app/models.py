from sqlalchemy import Column, Integer, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ProcessedData(Base):
    __tablename__ = "processed_data"
    id = Column(Integer, primary_key=True, index=True)
    utc_timestamp = Column(DateTime, index=True)
    mean = Column(Float)
    stddev = Column(Float)
