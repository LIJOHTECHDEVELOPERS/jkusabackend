# app/schemas/subscriber.py
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional

class SubscriberBase(BaseModel):
    """Base schema with common attributes"""
    email: EmailStr = Field(..., description="Subscriber's email address")

class SubscriberCreate(SubscriberBase):
    """Schema for creating a new subscriber (public endpoint)"""
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

class SubscriberUpdate(BaseModel):
    """Schema for updating subscriber status (admin only)"""
    is_active: Optional[bool] = Field(None, description="Active subscription status")

class Subscriber(SubscriberBase):
    """Schema for subscriber response"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_active": True,
                "subscribed_at": "2025-01-15T10:30:00Z",
                "unsubscribed_at": None
            }
        }
    )
    
    id: int = Field(..., description="Unique subscriber ID")
    is_active: bool = Field(..., description="Whether subscription is active")
    subscribed_at: datetime = Field(..., description="Timestamp when user subscribed")
    unsubscribed_at: Optional[datetime] = Field(None, description="Timestamp when user unsubscribed")

class SubscriberStats(BaseModel):
    """Schema for subscriber statistics (admin dashboard)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_subscribers": 1500,
                "active_subscribers": 1342,
                "unsubscribed": 158
            }
        }
    )
    
    total_subscribers: int = Field(..., description="Total number of subscribers")
    active_subscribers: int = Field(..., description="Number of active subscribers")
    unsubscribed: int = Field(..., description="Number of unsubscribed users")

class SubscriberResponse(BaseModel):
    """Generic response schema for success messages"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Successfully subscribed to newsletter"
            }
        }
    )
    
    detail: str = Field(..., description="Response message")

class SubscriberListResponse(BaseModel):
    """Schema for paginated subscriber list response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1500,
                "skip": 0,
                "limit": 100,
                "subscribers": [
                    {
                        "id": 1,
                        "email": "user@example.com",
                        "is_active": True,
                        "subscribed_at": "2025-01-15T10:30:00Z",
                        "unsubscribed_at": None
                    }
                ]
            }
        }
    )
    
    total: int = Field(..., description="Total number of subscribers")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")
    subscribers: list[Subscriber] = Field(..., description="List of subscribers")

class UnsubscribeRequest(BaseModel):
    """Schema for unsubscribe request"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "reason": "Too many emails"
            }
        }
    )
    
    email: EmailStr = Field(..., description="Email address to unsubscribe")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for unsubscribing")
    
    @field_validator('email')
    @classmethod
    def email_to_lowercase(cls, v):
        """Convert email to lowercase"""
        return v.lower()

class BulkSubscriberCreate(BaseModel):
    """Schema for bulk subscriber import (admin only)"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "emails": [
                    "user1@example.com",
                    "user2@example.com",
                    "user3@example.com"
                ]
            }
        }
    )
    
    emails: list[EmailStr] = Field(..., min_length=1, max_length=1000, description="List of email addresses")
    
    @field_validator('emails')
    @classmethod
    def emails_to_lowercase(cls, v):
        """Convert all emails to lowercase"""
        return [email.lower() for email in v]

class BulkSubscriberResponse(BaseModel):
    """Schema for bulk subscriber import response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_processed": 100,
                "successful": 95,
                "failed": 2,
                "duplicates": 3,
                "errors": [
                    "invalid@email: Invalid email format",
                    "duplicate@email.com: Already subscribed"
                ]
            }
        }
    )
    
    total_processed: int = Field(..., description="Total emails processed")
    successful: int = Field(..., description="Number of successful subscriptions")
    failed: int = Field(..., description="Number of failed subscriptions")
    duplicates: int = Field(..., description="Number of duplicate emails")
    errors: list[str] = Field(default=[], description="List of error messages")

class SubscriberExport(BaseModel):
    """Schema for exporting subscriber data"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "is_active": "Yes",
                "subscribed_at": "2025-01-15 10:30:00",
                "unsubscribed_at": ""
            }
        }
    )
    
    email: str
    is_active: bool
    subscribed_at: str
    unsubscribed_at: Optional[str] = None