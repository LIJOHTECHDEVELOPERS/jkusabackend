from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class studentCreate(BaseModel):
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[constr(min_length=10, max_length=15)]
    registration_number: constr(min_length=5, max_length=20)
    college_id: int
    school_id: int
    course: constr(min_length=1, max_length=100)
    year_of_study: int
    password: constr(min_length=8)

class studentLogin(BaseModel):
    login_id: str  # Email or Registration Number
    password: str

class studentResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    registration_number: str
    college_id: int
    school_id: int
    course: str
    year_of_study: int
    is_active: bool

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    user_id: int
    email: str