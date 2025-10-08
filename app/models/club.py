# app/models/club.py
from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    description = Column(Text)
    logo_url = Column(String, nullable=True)
    slug = Column(String, unique=True, index=True)