from pydantic import BaseModel, field_validator, ConfigDict
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    title: str
    description: str
    start_date: datetime  # Changed from 'date' to 'start_date'
    end_date: Optional[datetime] = None  # New: optional end_date
    location: str
    image_url: Optional[str] = None
    slug: str

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        """Ensure end_date is not before start_date"""
        if v is not None and 'start_date' in info.data:
            if v < info.data['start_date']:
                raise ValueError('end_date must be equal to or after start_date')
        return v

class EventCreate(EventBase):
    pass

class Event(EventBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int