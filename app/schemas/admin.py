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

class AdminUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class AdminRoleInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[List[str]] = None  # Changed to List[str] to match frontend expectation
    
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
    has_next: bool
    has_prev: bool