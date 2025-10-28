"""
ENHANCED MODELS - Backward compatible with your existing code
This adds advanced features while maintaining your current API
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum as SQLEnum, Table, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base

# ========== ENUMS ==========
class FormStatus(str, Enum):
    draft = "draft"
    open = "open"
    closed = "closed"
    archived = "archived"  # NEW

class FieldType(str, Enum):
    # Basic types (your existing)
    text = "text"
    boolean = "boolean"
    number = "number"
    select = "select"
    date = "date"
    textarea = "textarea"
    email = "email"
    
    # ENHANCED TYPES
    phone = "phone"
    currency = "currency"
    time = "time"
    datetime = "datetime"
    multi_select = "multi_select"
    radio = "radio"
    checkbox = "checkbox"
    file_upload = "file_upload"
    multi_file_upload = "multi_file_upload"
    address = "address"
    rating = "rating"
    country = "country"
    state = "state"

class ConditionType(str, Enum):
    """Types of conditions"""
    show = "show"
    hide = "hide"
    require = "require"
    disable = "disable"

class SubmissionStatus(str, Enum):
    """Submission states"""
    draft = "draft"
    submitted = "submitted"
    reviewed = "reviewed"
    approved = "approved"
    rejected = "rejected"

# ========== ASSOCIATION TABLES ==========
form_school_assignment = Table(
    'form_school_assignment',
    Base.metadata,
    Column('form_id', Integer, ForeignKey('form.id', ondelete='CASCADE'), primary_key=True),
    Column('school_id', Integer, ForeignKey('schools.id', ondelete='CASCADE'), primary_key=True)
)

form_year_assignment = Table(
    'form_year_assignment',
    Base.metadata,
    Column('form_id', Integer, ForeignKey('form.id', ondelete='CASCADE'), primary_key=True),
    Column('year_of_study', Integer, primary_key=True)
)

# ========== CORE MODELS ==========
class Form(Base):
    """Enhanced Form model - backward compatible with existing code"""
    __tablename__ = "form"
    
    # Original fields
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('admins.id'), nullable=False)
    open_date = Column(DateTime, nullable=False)
    close_date = Column(DateTime, nullable=False)
    status = Column(SQLEnum(FormStatus), default=FormStatus.draft, index=True)
    target_all_students = Column(Boolean, default=False)
    target_years = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ENHANCED FIELDS
    allow_multiple_submissions = Column(Boolean, default=False)
    require_authentication = Column(Boolean, default=True)
    enable_progress_bar = Column(Boolean, default=True)
    enable_conditional_logic = Column(Boolean, default=True)
    collect_ip_address = Column(Boolean, default=False)
    randomize_field_order = Column(Boolean, default=False)
    form_type = Column(String(50), default="registration")  # registration, survey, application
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    
    # Relationships
    fields = relationship(
        "FormField",
        back_populates="form",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="FormField.form_id"
    )
    submissions = relationship(
        "FormSubmission",
        back_populates="form",
        cascade="all, delete-orphan",
        foreign_keys="FormSubmission.form_id"
    )
    assigned_schools = relationship(
        "School",
        secondary=form_school_assignment,
        lazy="selectin"
    )
    notifications = relationship(
        "FormNotification",
        back_populates="form",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "FormAuditLog",
        back_populates="form",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_form_status_dates', 'status', 'open_date', 'close_date'),
    )
    
    def __repr__(self):
        return f"<Form(id={self.id}, title={self.title}, status={self.status})>"


class FormField(Base):
    """Enhanced FormField - backward compatible"""
    __tablename__ = "form_field"
    
    # Original fields
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(255), nullable=False)
    field_type = Column(SQLEnum(FieldType), nullable=False)
    required = Column(Boolean, default=False)
    options = Column(JSON, nullable=True)
    default_value = Column(String(255), nullable=True)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # ENHANCED FIELDS
    description = Column(Text, nullable=True)
    placeholder = Column(String(255), nullable=True)
    help_text = Column(Text, nullable=True)
    
    # Validation rules
    min_value = Column(Integer, nullable=True)
    max_value = Column(Integer, nullable=True)
    min_length = Column(Integer, nullable=True)
    max_length = Column(Integer, nullable=True)
    validation_rules = Column(JSON, default=dict)
    
    # File upload config
    file_upload_config = Column(JSON, nullable=True)
    # {
    #   "allowed_types": ["pdf", "doc", "image"],
    #   "max_size": 10485760,
    #   "accept_multiple": false
    # }
    
    # UI configuration
    width_percentage = Column(Integer, default=100)
    is_section_header = Column(Boolean, default=False)
    section_description = Column(Text, nullable=True)
    
    # Conditional logic
    depends_on_field_id = Column(Integer, ForeignKey('form_field.id'), nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="fields", foreign_keys=[form_id])
    conditions = relationship(
        "FormCondition",
        foreign_keys="FormCondition.field_id",
        back_populates="field",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    dependent_conditions = relationship(
        "FormCondition",
        foreign_keys="FormCondition.depends_on_field_id",
        back_populates="depends_on_field",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index('idx_field_form_position', 'form_id', 'position'),
        Index('idx_field_type', 'field_type'),
    )
    
    def __repr__(self):
        return f"<FormField(id={self.id}, label={self.label}, type={self.field_type})>"


class FormCondition(Base):
    """Enhanced FormCondition with more operators"""
    __tablename__ = "form_condition"
    
    # Original fields
    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey('form_field.id', ondelete='CASCADE'), nullable=False)
    depends_on_field_id = Column(Integer, ForeignKey('form_field.id'), nullable=False)
    operator = Column(String(50), nullable=False)
    # Operators: equals, not_equals, contains, greater_than, less_than, 
    #            is_empty, is_not_empty, in_list, not_in_list
    value = Column(String(255), nullable=False)
    
    # ENHANCED FIELDS
    condition_type = Column(SQLEnum(ConditionType), default=ConditionType.show)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    field = relationship(
        "FormField",
        foreign_keys=[field_id],
        back_populates="conditions",
        lazy="selectin"
    )
    depends_on_field = relationship(
        "FormField",
        foreign_keys=[depends_on_field_id],
        back_populates="dependent_conditions",
        lazy="selectin"
    )
    
    __table_args__ = (
        Index('idx_condition_dependencies', 'field_id', 'depends_on_field_id'),
    )
    
    def __repr__(self):
        return f"<FormCondition(id={self.id}, type={self.condition_type})>"


class FormSubmission(Base):
    """Enhanced FormSubmission with file tracking"""
    __tablename__ = "form_submission"
    
    # Original fields
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    data = Column(JSON, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_edited_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    locked = Column(Boolean, default=False)
    
    # ENHANCED FIELDS
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.submitted)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    time_to_complete_seconds = Column(Integer, nullable=True)
    
    # Review workflow
    reviewed_by = Column(Integer, ForeignKey('admins.id'), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Relationships
    form = relationship("Form", back_populates="submissions", foreign_keys=[form_id])
    student = relationship("student", back_populates="form_submissions", foreign_keys=[student_id])
    file_uploads = relationship(
        "FormFieldUpload",
        back_populates="submission",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_submission_form_user', 'form_id', 'student_id'),
        Index('idx_submission_status', 'status', 'submitted_at'),
    )
    
    def __repr__(self):
        return f"<FormSubmission(id={self.id}, form_id={self.form_id}, status={self.status})>"


# ========== NEW MODELS FOR ADVANCED FEATURES ==========
class FormFieldUpload(Base):
    """Track file uploads from form submissions"""
    __tablename__ = "form_field_upload"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey('form_submission.id', ondelete='CASCADE'), nullable=False)
    field_id = Column(Integer, ForeignKey('form_field.id'), nullable=False)
    
    # File information
    original_filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_type = Column(String(50), nullable=False)  # pdf, doc, image, etc
    content_type = Column(String(100), nullable=False)
    
    # S3 storage
    s3_key = Column(String(500), nullable=False, index=True)
    s3_url = Column(String(1000), nullable=False)
    
    # Metadata
    upload_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    file_hash = Column(String(64), nullable=True)
    virus_scan_status = Column(String(50), default="pending")  # pending, clean, infected
    
    # Relationships
    submission = relationship("FormSubmission", back_populates="file_uploads")
    
    __table_args__ = (
        Index('idx_upload_submission_field', 'submission_id', 'field_id'),
    )


class FormNotification(Base):
    """Configure notifications for form submissions"""
    __tablename__ = "form_notification"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    
    # Notification settings
    notify_on_submission = Column(Boolean, default=True)
    notify_on_review = Column(Boolean, default=False)
    notification_recipients = Column(JSON, default=list)  # [email1, email2]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    form = relationship("Form", back_populates="notifications")


class FormAuditLog(Base):
    """Audit trail for form changes"""
    __tablename__ = "form_audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey('form.id', ondelete='CASCADE'), nullable=False)
    admin_id = Column(Integer, ForeignKey('admins.id'), nullable=False)
    
    action = Column(String(50), nullable=False)  # create, update, delete, publish, close
    entity_type = Column(String(50), nullable=False)  # form, field, submission
    entity_id = Column(Integer, nullable=True)
    changes = Column(JSON, nullable=True)  # {field: {old: x, new: y}}
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_audit_form_timestamp', 'form_id', 'timestamp'),
    )