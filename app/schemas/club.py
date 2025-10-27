# app/schemas/club.py
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ClubCreate(BaseModel):
    name: str
    description: str

class Club(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: str
    logo_url: Optional[str] = None
    slug: str