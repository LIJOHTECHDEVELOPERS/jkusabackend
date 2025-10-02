# app/schemas/activity.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ActivityBase(BaseModel):
    title: str
    description: str
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None
    featured_image_url: Optional[str] = None
    published_at: datetime
    publisher_id: int

class ActivityCreate(BaseModel):
    title: str
    description: str
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None

class ActivityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = None

class Activity(ActivityBase):
    id: int

    class Config:
        from_attributes = True