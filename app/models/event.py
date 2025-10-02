from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    date = Column(DateTime)
    location = Column(String)
    image_url = Column(String, nullable=True)  # Added image_url field