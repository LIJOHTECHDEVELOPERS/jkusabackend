"""
Pydantic Schemas for Student Authentication
File: app/schemas/student.py
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import re


class studentCreate(BaseModel):
    """Schema for student registration"""
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=15)
    registration_number: str = Field(..., min_length=5, max_length=20)
    college_id: int = Field(..., gt=0)
    school_id: int = Field(..., gt=0)
    course: str = Field(..., min_length=3, max_length=100)
    year_of_study: int = Field(..., ge=1, le=6)
    password: str = Field(..., min_length=8, max_length=128)
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if not re.match(r"^[a-zA-Z\s'-]+$", v):
            raise ValueError('Name must contain only letters, spaces, hyphens, and apostrophes')
        return v.strip()
    
    @validator('phone_number')
    def validate_phone(cls, v):
        # Remove spaces and special characters
        phone = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', phone):
            raise ValueError('Invalid phone number format')
        return phone
    
    @validator('registration_number')
    def validate_reg_number(cls, v):
        # Basic validation - adjust based on your institution's format
        v = v.strip().upper()
        if not re.match(r'^[A-Z0-9\-/]+$', v):
            raise ValueError('Registration number contains invalid characters')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@students.jkuat.ac.ke",
                "phone_number": "+254712345678",
                "registration_number": "SCT211-0001/2021",
                "college_id": 1,
                "school_id": 1,
                "course": "Computer Science",
                "year_of_study": 3,
                "password": "SecurePass123!"
            }
        }


class studentLogin(BaseModel):
    """Schema for student login"""
    login_id: str = Field(..., description="Email or Registration Number")
    password: str = Field(..., min_length=1)
    
    class Config:
        schema_extra = {
            "example": {
                "login_id": "john.doe@students.jkuat.ac.ke",
                "password": "SecurePass123!"
            }
        }


class studentResponse(BaseModel):
    """Schema for student response (excludes sensitive data)"""
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    registration_number: str
    college_id: int
    school_id: int
    course: str
    year_of_study: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@students.jkuat.ac.ke",
                "phone_number": "+254712345678",
                "registration_number": "SCT211-0001/2021",
                "college_id": 1,
                "school_id": 1,
                "course": "Computer Science",
                "year_of_study": 3,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00",
                "last_login": "2024-01-20T14:45:00",
                "email_verified_at": "2024-01-15T11:00:00"
            }
        }


class TokenData(BaseModel):
    """Schema for JWT token data"""
    student_id: int
    email: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr
    
    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@students.jkuat.ac.ke"
            }
        }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123-def456-ghi789",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    class Config:
        schema_extra = {
            "example": {
                "old_password": "OldPassword123!",
                "new_password": "NewSecurePass123!",
                "confirm_password": "NewSecurePass123!"
            }
        }


class CollegeResponse(BaseModel):
    """Schema for college response"""
    id: int
    name: str
    
    class Config:
        orm_mode = True


class SchoolResponse(BaseModel):
    """Schema for school response"""
    id: int
    name: str
    college_id: int
    
    class Config:
        orm_mode = True