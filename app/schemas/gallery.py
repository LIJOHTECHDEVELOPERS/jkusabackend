from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.gallery import GalleryCategory

class GalleryBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: GalleryCategory
    year: Optional[str] = None
    display_order: int = Field(default=0, ge=0)

class GalleryCreate(GalleryBase):
    pass

class GalleryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[GalleryCategory] = None
    year: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)

class Gallery(GalleryBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class GalleryReorderRequest(BaseModel):
    gallery_items: List[dict]  # [{"id": 1, "display_order": 0}, ...]

class CategoryGalleryResponse(BaseModel):
    category: str
    count: int
    items: List[Gallery]

class GallerySummary(BaseModel):
    total_count: int
    categories: dict  # {"POLITICS": 10, "SPORTS": 15, ...}
    years: List[str]