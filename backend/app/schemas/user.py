from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: str = "editor"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
