## app/schemas/resource.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

class ResourceCreate(BaseModel):
    title: str
    description: str

class Resource(ResourceCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    pdf_url: Optional[str] = None
    slug: str