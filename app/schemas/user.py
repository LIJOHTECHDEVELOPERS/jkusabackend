from pydantic import BaseModel, ConfigDict

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str