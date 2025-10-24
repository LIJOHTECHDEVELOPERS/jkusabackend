"""
SQLAlchemy Models for Student Authentication
File: app/models/student.py
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class College(Base):
    """College model"""
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    schools = relationship("School", back_populates="college", cascade="all, delete-orphan")
    students = relationship("student", back_populates="college")

    def __repr__(self):
        return f"<College(id={self.id}, name='{self.name}')>"

class School(Base):
    """School model"""
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    college = relationship("College", back_populates="schools")
    students = relationship("student", back_populates="school")

    # Indexes
    __table_args__ = (
        Index('idx_school_college', 'college_id'),
        Index('idx_school_name', 'name'),
    )

    def __repr__(self):
        return f"<School(id={self.id}, name='{self.name}', college_id={self.college_id})>"

class FormSubmission(Base):
    """FormSubmission model"""
    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    # Add other fields as needed for form submissions

    # Relationships
    student = relationship("student", back_populates="form_submissions")

class student(Base):
    """Student model with comprehensive authentication fields"""
    __tablename__ = "students"

    # Primary Fields
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    registration_number = Column(String(50), unique=True, nullable=False, index=True)

    # Academic Information
    college_id = Column(Integer, ForeignKey("colleges.id", ondelete="RESTRICT"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="RESTRICT"), nullable=False)
    course = Column(String(100), nullable=False)
    year_of_study = Column(Integer, nullable=False)

    # Authentication Fields
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

    # Email Verification
    verification_token = Column(String(255), unique=True, nullable=True)
    verification_token_expiry = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Password Reset
    password_reset_token = Column(String(255), unique=True, nullable=True)
    password_reset_token_expiry = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Security Fields (optional - for advanced security)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    college = relationship("College", back_populates="students")
    school = relationship("School", back_populates="students")
    form_submissions = relationship("FormSubmission", back_populates="student", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_student_email', 'email'),
        Index('idx_student_reg_number', 'registration_number'),
        Index('idx_student_college', 'college_id'),
        Index('idx_student_school', 'school_id'),
        Index('idx_student_active', 'is_active'),
        Index('idx_verification_token', 'verification_token'),
        Index('idx_reset_token', 'password_reset_token'),
    )

    def __repr__(self):
        return f"<Student(id={self.id}, email='{self.email}', reg_number='{self.registration_number}')>"

    @property
    def full_name(self):
        """Get student's full name"""
        return f"{self.first_name} {self.last_name}"

    def is_email_verified(self):
        """Check if email is verified"""
        return self.email_verified_at is not None

    def is_account_locked(self):
        """Check if account is locked"""
        if self.locked_until and self.locked_until > func.now():
            return True
        return False
