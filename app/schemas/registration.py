"""
ENHANCED SCHEMAS - Backward compatible with your existing code
All new fields are optional to maintain backward compatibility
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ========== ENUMS ==========
class FieldType(str, Enum):
    # Your existing types
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"
    SELECT = "select"
    DATE = "date"
    TEXTAREA = "textarea"
    EMAIL = "email"
    
    # NEW TYPES
    PHONE = "phone"
    CURRENCY = "currency"
    TIME = "time"
    DATETIME = "datetime"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE_UPLOAD = "file_upload"
    MULTI_FILE_UPLOAD = "multi_file_upload"
    ADDRESS = "address"
    RATING = "rating"
    COUNTRY = "country"
    STATE = "state"

class FormStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"

class ConditionType(str, Enum):
    SHOW = "show"
    HIDE = "hide"
    REQUIRE = "require"
    DISABLE = "disable"

class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"

# ========== FILE UPLOAD SCHEMAS ==========
class FileUploadConfig(BaseModel):
    """Configuration for file upload fields"""
    allowed_types: List[str] = Field(
        default=["pdf", "doc", "image"],
        description="pdf, doc, image, video, spreadsheet, archive"
    )
    max_size: int = Field(default=10485760, description="Max size in bytes")
    accept_multiple: bool = False

class FormFieldUploadResponse(BaseModel):
    """Response for uploaded file"""
    id: int
    original_filename: str
    file_size: int
    file_type: str
    s3_url: str
    upload_timestamp: datetime
    virus_scan_status: str
    
    model_config = ConfigDict(from_attributes=True)

# ========== CONDITION SCHEMAS ==========
class FormConditionCreate(BaseModel):
    """Create form condition"""
    depends_on_field_id: int
    operator: str  # equals, not_equals, contains, greater_than, less_than, is_empty, is_not_empty
    value: str
    condition_type: Optional[str] = ConditionType.SHOW  # NEW: Optional for backward compatibility

class FormConditionResponse(BaseModel):
    """Form condition response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    field_id: int
    depends_on_field_id: int
    operator: str
    value: str
    condition_type: str

# ========== FIELD SCHEMAS ==========
class FormFieldCreate(BaseModel):
    """Create form field - enhanced with optional new fields"""
    label: str = Field(..., min_length=1, max_length=255)
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    position: int = 0
    conditions: Optional[List[FormConditionCreate]] = Field(default_factory=list)
    
    # ENHANCED OPTIONAL FIELDS
    description: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    file_upload_config: Optional[FileUploadConfig] = None
    width_percentage: Optional[int] = 100
    is_section_header: Optional[bool] = False
    section_description: Optional[str] = None
    depends_on_field_id: Optional[int] = None
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        field_type = info.data.get('field_type')
        if field_type in [FieldType.SELECT, FieldType.RADIO, FieldType.MULTI_SELECT, FieldType.CHECKBOX]:
            if not v or len(v) == 0:
                raise ValueError(f"{field_type} field must have options")
        return v
    
    @field_validator('file_upload_config')
    @classmethod
    def validate_file_config(cls, v, info):
        field_type = info.data.get('field_type')
        if field_type in [FieldType.FILE_UPLOAD, FieldType.MULTI_FILE_UPLOAD] and not v:
            raise ValueError(f"{field_type} field must have file_upload_config")
        return v

class FormFieldUpdate(BaseModel):
    """Update form field - all fields optional"""
    label: Optional[str] = None
    field_type: Optional[FieldType] = None
    required: Optional[bool] = None
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    position: Optional[int] = None
    conditions: Optional[List[FormConditionCreate]] = None
    description: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None
    file_upload_config: Optional[FileUploadConfig] = None
    width_percentage: Optional[int] = None
    depends_on_field_id: Optional[int] = None

class FormFieldResponse(FormFieldCreate):
    """Form field response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    created_at: datetime
    conditions: List[FormConditionResponse] = Field(default_factory=list)

# Backward compatibility alias
FormFieldSchema = FormFieldResponse

# ========== FORM SCHEMAS ==========
class FormCreate(BaseModel):
    """Create form - enhanced with optional new fields"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    open_date: datetime
    close_date: datetime
    target_all_students: bool = False
    target_school_ids: Optional[List[int]] = Field(default_factory=list)
    target_years: Optional[List[int]] = Field(default_factory=list)
    fields: List[FormFieldCreate]
    status: Optional[FormStatus] = FormStatus.DRAFT
    
    # ENHANCED OPTIONAL FIELDS
    allow_multiple_submissions: Optional[bool] = False
    require_authentication: Optional[bool] = True
    enable_progress_bar: Optional[bool] = True
    enable_conditional_logic: Optional[bool] = True
    collect_ip_address: Optional[bool] = False
    randomize_field_order: Optional[bool] = False
    form_type: Optional[str] = "registration"
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('close_date')
    @classmethod
    def validate_close_date(cls, v, info):
        if 'open_date' in info.data and v <= info.data['open_date']:
            raise ValueError("Close date must be after open date")
        return v

class FormUpdate(BaseModel):
    """Update form - all fields optional"""
    title: Optional[str] = None
    description: Optional[str] = None
    open_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    target_all_students: Optional[bool] = None
    target_school_ids: Optional[List[int]] = None
    target_years: Optional[List[int]] = None
    status: Optional[FormStatus] = None
    allow_multiple_submissions: Optional[bool] = None
    enable_progress_bar: Optional[bool] = None
    enable_conditional_logic: Optional[bool] = None
    randomize_field_order: Optional[bool] = None
    tags: Optional[List[str]] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

class FormResponse(BaseModel):
    """Form response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    created_by: int
    open_date: datetime
    close_date: datetime
    status: FormStatus
    target_all_students: bool
    target_years: List[int]
    created_at: datetime
    updated_at: datetime
    fields: List[FormFieldResponse]
    
    # ENHANCED OPTIONAL RESPONSE FIELDS
    allow_multiple_submissions: Optional[bool] = None
    require_authentication: Optional[bool] = None
    enable_progress_bar: Optional[bool] = None
    enable_conditional_logic: Optional[bool] = None
    collect_ip_address: Optional[bool] = None
    randomize_field_order: Optional[bool] = None
    form_type: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

# ========== SUBMISSION SCHEMAS ==========
class FormSubmissionCreate(BaseModel):
    """Create form submission"""
    data: Dict[int, Any]

class FormSubmissionUpdate(BaseModel):
    """Update form submission"""
    data: Dict[int, Any]

class FormSubmissionResponse(BaseModel):
    """Form submission response - backward compatible"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    submitted_by: int
    submitted_at: datetime
    data: Dict[int, Any]
    
    # ENHANCED OPTIONAL RESPONSE FIELDS
    status: Optional[SubmissionStatus] = None
    locked: Optional[bool] = None
    last_edited_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    time_to_complete_seconds: Optional[int] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    file_uploads: Optional[List[FormFieldUploadResponse]] = Field(default_factory=list)

# ========== ANALYTICS SCHEMAS ==========
class FieldAnalytics(BaseModel):
    """Schema for individual field analytics"""
    model_config = ConfigDict(from_attributes=True)
    
    field_id: int
    field_label: str
    field_type: str
    total_responses: int
    response_breakdown: Dict[str, Any]

class FormAnalyticsResponse(BaseModel):
    """Form analytics response"""
    model_config = ConfigDict(from_attributes=True)
    
    form_id: int
    form_title: str
    total_submissions: int
    submission_percentage: float
    submission_deadline: datetime
    field_analytics: List[FieldAnalytics]
    ai_summary: Optional[str] = None
    ai_insights: Optional[str] = None

# ========== NOTIFICATION SCHEMAS ==========
class FormNotificationConfig(BaseModel):
    """Form notification configuration"""
    notify_on_submission: bool = True
    notify_on_review: bool = False
    notification_recipients: List[str]

class FormNotificationResponse(BaseModel):
    """Form notification response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    notify_on_submission: bool
    notify_on_review: bool
    notification_recipients: List[str]
    created_at: datetime

# ========== AUDIT LOG SCHEMAS ==========
class FormAuditLogResponse(BaseModel):
    """Form audit log response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    admin_id: int
    action: str
    entity_type: str
    entity_id: Optional[int]
    changes: Optional[Dict[str, Any]]
    timestamp: datetime