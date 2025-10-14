from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class AdminRole(Base):
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    permissions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    admins = relationship("Admin", back_populates="role")
    
    def __repr__(self):
        return f"<AdminRole(id={self.id}, name='{self.name}')>"