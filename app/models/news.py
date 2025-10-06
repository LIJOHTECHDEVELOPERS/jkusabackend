# app/models/news.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base
import re

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    slug = Column(String(300), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    featured_image_url = Column(String(500), nullable=True)  # URL to S3 object
    published_at = Column(DateTime, nullable=False)
    publisher_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    
    # Relationship to Admin (Publisher)
    publisher = relationship("Admin", back_populates="published_news")
    
    @staticmethod
    def generate_slug(title: str) -> str:
        """Generate a URL-friendly slug from title"""
        slug = title.lower()
        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = re.sub(r'^-+|-+$', '', slug)
        # Limit to 300 characters
        return slug[:300]
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', slug='{self.slug}', publisher_id={self.publisher_id})>"