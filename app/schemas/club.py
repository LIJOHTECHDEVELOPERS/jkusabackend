# app/schemas/club.py
from typing import Optional
from pydantic import BaseModel

class ClubCreate(BaseModel):
    name: str
    description: str

class Club(BaseModel):
    id: int
    name: str
    description: str
    logo_url: Optional[str]
    slug: str

    class Config:
        from_attributes = True