from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    title: str
    description: str
    date: datetime
    location: str
    image_url: Optional[str] = None  # Added image_url field

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    class Config:
        from_attributes = True