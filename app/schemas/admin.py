from pydantic import BaseModel

class AdminCreate(BaseModel):
    username: str
    password: str

class Admin(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True  # For Pydantic v2 compatibility with SQLAlchemy

class Token(BaseModel):
    access_token: str
    token_type: str