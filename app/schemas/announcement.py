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
    admin_id: int
    announced_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True