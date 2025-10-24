# ==================== MODELS ====================
# app/models/registration.py

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum, Table, select
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base

class FormStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"

class FieldType(str, Enum):
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"
    SELECT = "select"
    DATE = "date"
    TEXTAREA = "textarea"
    EMAIL = "email"

# Association table for form assignment to schools
form_school_assignment = Table(
    'form_school_assignment',
    Base.metadata,
    Column('form_id', Integer, ForeignKey('form.id', ondelete='CASCADE')),
    Column('school_id', Integer, ForeignKey('school.id', ondelete='CASCADE'))
)

# Association table for form assignment to years
form_year_assignment = Table(
    'form_year_assignment',
    Base.metadata,
    Column('form_id', Integer, ForeignKey('form.id', ondelete='CASCADE')),
    Column('year_of_study', Integer)
)

class Form(Base):
    __tablename__ = "form"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('admin.id'), nullable=False)
    open_date = Column(DateTime, nullable=False)
    close_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(FormStatus), default=FormStatus.DRAFT, index=True)
    target_all_students = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan", lazy="selectin")
    submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")
    assigned_schools = relationship("School", secondary=form_school_assignment, lazy="selectin")
    
    # Store years as JSON for flexibility
    target_years = Column(JSON, default=list)  # [1, 2, 3, 4, 5, 6]
    
    def __repr__(self):
        return f"<Form(id={self.id}, title={self.title}, status={self.status})>"

class FormField(Base):
    __tablename__ = "form_field"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(255), nullable=False)
    field_type = Column(SQLEnum(FieldType), nullable=False)
    required = Column(Boolean, default=False)
    options = Column(JSON, nullable=True)  # For select fields: ["Option1", "Option2"]
    default_value = Column(String(255), nullable=True)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    form = relationship("Form", back_populates="fields")
    conditions = relationship("FormCondition", back_populates="field", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<FormField(id={self.id}, form_id={self.form_id}, label={self.label})>"

class FormCondition(Base):
    __tablename__ = "form_condition"
    
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey('form_field.id', ondelete='CASCADE'), nullable=False)
    depends_on_field_id = Column(Integer, ForeignKey('form_field.id'), nullable=False)
    operator = Column(String(50), nullable=False)  # "equals", "not_equals", "contains", etc.
    value = Column(String(255), nullable=False)
    
    # Relationships
    field = relationship("FormField", back_populates="conditions", foreign_keys=[field_id])
    
    def __repr__(self):
        return f"<FormCondition(id={self.id}, depends_on={self.depends_on_field_id})>"

class FormSubmission(Base):
    __tablename__ = "form_submission"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('student.id', ondelete='CASCADE'), nullable=False)
    data = Column(JSON, nullable=False)  # {field_id: value, ...}
    submitted_at = Column(DateTime, default=datetime.utcnow)
    last_edited_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    locked = Column(Boolean, default=False)
    
    # Relationships
    form = relationship("Form", back_populates="submissions")
    student = relationship("Student", back_populates="form_submissions")
    
    def __repr__(self):
        return f"<FormSubmission(id={self.id}, form_id={self.form_id}, student_id={self.student_id})>"