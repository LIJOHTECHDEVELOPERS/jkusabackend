from pydantic import BaseModel, Field
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
    title: str = Field(..., min_length=10, max_length=255)
    slug: Optional[str] = None
    content: str = Field(..., min_length=50)
    featured_image_url: Optional[str] = None
    published_at: datetime

class NewsCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=255)
    content: str = Field(..., min_length=50)
    featured_image_url: Optional[str] = None
    published_at: datetime
    # slug is auto-generated, not provided during creation

class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=10, max_length=255)
    content: Optional[str] = Field(None, min_length=50)
    featured_image_url: Optional[str] = None
    published_at: Optional[datetime] = None
    # slug is auto-updated when title changes

class News(NewsBase):
    id: int
    slug: str  # Required in response
    publisher_id: int
    publisher: PublisherInfo
    
    class Config:
        from_attributes = True