# app/schemas/announcement.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnnouncementBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class Announcement(AnnouncementBase):
    id: int
    announced_at: datetime

    class Config:
        from_attributes = True