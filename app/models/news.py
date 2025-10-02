# app/models/news.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)
    featured_image_url = Column(String(500), nullable=True)  # URL to S3 object
    published_at = Column(DateTime, nullable=False)
    publisher_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    
    # Relationship to Admin (Publisher)
    publisher = relationship("Admin", back_populates="published_news")
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', publisher_id={self.publisher_id})>"
