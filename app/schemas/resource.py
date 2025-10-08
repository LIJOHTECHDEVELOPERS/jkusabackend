## app/schemas/resource.py
from pydantic import BaseModel
from typing import Optional

class ResourceCreate(BaseModel):
    title: str
    description: str

class Resource(ResourceCreate):
    id: int
    pdf_url: Optional[str]
    slug: str