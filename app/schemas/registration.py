# ==================== SCHEMAS ====================
# app/schemas/registration.py

from pydantic import BaseModel, Field, validator
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

# ========== Field Schemas ==========
class FormConditionCreate(BaseModel):
    depends_on_field_id: int
    operator: str  # "equals", "not_equals", "contains"
    value: str

class FormCondition(FormConditionCreate):
    id: int
    field_id: int
    
    class Config:
        from_attributes = True

class FormFieldCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=255)
    field_type: FieldType
    required: bool = False
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    position: int = 0
    conditions: Optional[List[FormConditionCreate]] = []
    
    @validator('options')
    def validate_options(cls, v, values):
        if values.get('field_type') == FieldType.SELECT and (not v or len(v) == 0):
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
    id: int
    form_id: int
    created_at: datetime
    conditions: List[FormCondition] = []
    
    class Config:
        from_attributes = True

# ========== Form Schemas ==========
class FormCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    open_date: datetime
    close_date: datetime
    target_all_students: bool = False
    target_school_ids: Optional[List[int]] = []
    target_years: Optional[List[int]] = []
    fields: List[FormFieldCreate]
    
    @validator('close_date')
    def validate_close_date(cls, v, values):
        if 'open_date' in values and v <= values['open_date']:
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

class FormResponse(BaseModel):
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
    
    class Config:
        from_attributes = True