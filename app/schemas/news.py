from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PublisherInfo(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    
    class Config:
        from_attributes = True

class NewsBase(BaseModel):
    title: str
    content: str
    featured_image_url: Optional[str] = None
    published_at: datetime

class NewsCreate(BaseModel):
    title: str
    content: str
    featured_image_url: Optional[str] = None
    published_at: datetime

class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    featured_image_url: Optional[str] = None
    published_at: Optional[datetime] = None

class News(NewsBase):
    id: int
    publisher_id: int
    publisher: PublisherInfo
    
    class Config:
        from_attributes = True