from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Admin(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: str
    phone_number: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Activity(BaseModel):
    id: int
    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=50)
    start_datetime: datetime
    end_datetime: Optional[datetime]
    location: Optional[str] = Field(None, max_length=255)
    featured_image_url: Optional[str]
    published_at: datetime
    publisher_id: int
    publisher: Optional[Admin]

    class Config:
        orm_mode = True

class ActivityListResponse(BaseModel):
    items: List[Activity]
    total: int

class ActivityCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=50)
    start_datetime: str
    end_datetime: Optional[str]
    location: Optional[str] = Field(None, max_length=255)

class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=10, max_length=255)
    description: Optional[str] = Field(None, min_length=50)
    start_datetime: Optional[str]
    end_datetime: Optional[str]
    location: Optional[str] = Field(None, max_length=255)
    remove_image: Optional[str]