from pydantic import BaseModel
from typing import Optional, Dict, List

class AdminCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    username: str
    password: str
    role_id: Optional[int] = None

class AdminRoleInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class Admin(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    is_active: bool
    role: Optional[AdminRoleInfo] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user_data: Admin

class AdminListResponse(BaseModel):
    admins: List[Admin]
    total: int
    page: int
    per_page: int
    total_pages: int