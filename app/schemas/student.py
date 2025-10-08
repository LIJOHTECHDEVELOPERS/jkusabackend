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
    # FIX/ENHANCEMENT: Added max_length=72 to prevent the password hashing ValueError 
    # and provide immediate client-side feedback for overly long passwords.
    password: constr(min_length=8, max_length=72)

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
        # FIX: Pydantic V2 equivalent of orm_mode = True
        from_attributes = True

class TokenData(BaseModel):
    # FIX: Changed 'user_id' to 'student_id' to match the key used in your JWT creation logic
    student_id: int
    email: str