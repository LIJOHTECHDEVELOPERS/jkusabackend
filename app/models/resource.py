from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    pdf_url = Column(String, nullable=True)
    slug = Column(String, unique=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    
    publisher = relationship("Admin", back_populates="published_resources")