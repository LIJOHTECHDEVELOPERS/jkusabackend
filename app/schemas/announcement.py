from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class AnnouncementBase(BaseModel):
    title: str
    content: str
    image_url: Optional[str] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class Announcement(AnnouncementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    admin_id: int
    announced_at: datetime
    updated_at: Optional[datetime] = None