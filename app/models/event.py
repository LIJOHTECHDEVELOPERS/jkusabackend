from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    start_date = Column(DateTime)  # Changed from 'date' to 'start_date'
    end_date = Column(DateTime, nullable=True)  # New: end_date for multi-day events
    location = Column(String)
    image_url = Column(String, nullable=True)
    slug = Column(String, unique=True, index=True, nullable=False)