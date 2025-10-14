from pydantic import BaseModel
from typing import Optional, Dict

class AdminRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict] = None

class AdminRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict] = None

class AdminRole(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True