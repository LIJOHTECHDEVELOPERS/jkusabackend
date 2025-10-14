from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    role = relationship("AdminRole", back_populates="admins")
    published_news = relationship("News", back_populates="publisher", cascade="all, delete-orphan")
    published_activities = relationship("Activity", back_populates="publisher")
    published_resources = relationship("Resource", back_populates="publisher", cascade="all, delete-orphan")
    
    def is_super_admin(self):
        """Check if admin has super_admin role"""
        return self.role.name == "super_admin" if self.role else False
    
    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}', email='{self.email}')>"