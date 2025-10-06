from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

class GalleryCategory(str, enum.Enum):
    POLITICS = "POLITICS"
    SPORTS = "SPORTS"
    EVENTS = "EVENTS"
    CLUBS = "CLUBS"
    ACADEMIC = "ACADEMIC"
    SOCIAL = "SOCIAL"
    CULTURAL = "CULTURAL"

class Gallery(Base):
    __tablename__ = "galleries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=False)
    category = Column(SQLEnum(GalleryCategory), nullable=False, index=True)
    year = Column(String(20), nullable=True, index=True)  # e.g., "2024", "2023-2024"
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Gallery(id={self.id}, title={self.title}, category={self.category})>"