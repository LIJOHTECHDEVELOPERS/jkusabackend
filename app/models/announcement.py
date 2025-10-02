# app/models/announcement.py
from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    image_url = Column(String, nullable=True)
    announced_at = Column(DateTime, default=datetime.utcnow)