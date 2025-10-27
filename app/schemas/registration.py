# app/schemas/registration.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class FieldType(str, Enum):
    TEXT = "text"
    BOOLEAN = "boolean"
    NUMBER = "number"
    SELECT = "select"
    DATE = "date"
    TEXTAREA = "textarea"
    EMAIL = "email"

class FormStatus(str, Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"

# -------------------- Field Schemas --------------------
class FormConditionCreate(BaseModel):
    depends_on_field_id: int
    operator: str  # "equals", "not_equals", "contains"
    value: str

class FormCondition(FormConditionCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    field_id: int

class FormFieldCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    position: int = 0
    conditions: Optional[List[FormConditionCreate]] = []
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        if info.data.get('field_type') == FieldType.SELECT and (not v or len(v) == 0):
            raise ValueError("Select field must have options")
        return v

class FormFieldUpdate(BaseModel):
    label: Optional[str] = None
    field_type: Optional[FieldType] = None
    required: Optional[bool] = None
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    position: Optional[int] = None
    conditions: Optional[List[FormConditionCreate]] = None

class FormField(FormFieldCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    created_at: datetime
    conditions: List[FormCondition] = []

# Alias for backwards compatibility
FormFieldSchema = FormField

# -------------------- Form Schemas --------------------
class FormCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    open_date: datetime
    close_date: datetime
    target_all_students: bool = False
    target_school_ids: Optional[List[int]] = []
    target_years: Optional[List[int]] = []
    fields: List[FormFieldCreate]
    status: Optional[FormStatus] = FormStatus.DRAFT
    
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
    title: Optional[str] = None
    description: Optional[str] = None
    open_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    target_all_students: Optional[bool] = None
    target_school_ids: Optional[List[int]] = None
    target_years: Optional[List[int]] = None
    status: Optional[FormStatus] = None
    
    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

class FormResponse(BaseModel):
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
    fields: List[FormField]

# -------------------- Submission Schemas --------------------
class FormSubmissionFieldData(BaseModel):
    """Represents a single field's data within a submission."""
    model_config = ConfigDict(from_attributes=True)
    
    field_id: int
    value: Any

class FormSubmissionCreate(BaseModel):
    """Represents the data sent by a user to create a new submission."""
    data: Dict[int, Any]

class FormSubmissionUpdate(BaseModel):
    """Represents data for updating an existing form submission."""
    model_config = ConfigDict(from_attributes=True)
    
    data: Dict[int, Any]

class FormSubmissionResponse(BaseModel):
    """Represents a full form submission retrieved from the database."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    form_id: int
    submitted_by: int
    submitted_at: datetime
    data: List[FormSubmissionFieldData]

# -------------------- Analytics Schemas --------------------
class FieldAnalytics(BaseModel):
    """Schema for individual field analytics within a form."""
    model_config = ConfigDict(from_attributes=True)
    
    field_id: int
    field_label: str
    field_type: str
    total_responses: int
    response_breakdown: Dict[str, Any]

class FormAnalyticsResponse(BaseModel):
    """
    Response schema for the form analytics endpoint.
    Contains aggregated analytics data for a form and its submissions.
    """
    model_config = ConfigDict(from_attributes=True)
    
    form_id: int
    form_title: str
    total_submissions: int
    submission_percentage: float
    submission_deadline: datetime
    field_analytics: List[FieldAnalytics]
    ai_summary: Optional[str] = None
    ai_insights: Optional[str] = None