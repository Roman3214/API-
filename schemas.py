from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from fastapi import HTTPException
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    @validator('password')
    def validate_password(cls, password):
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password should be at least 8 characters long")
        return password
    
class NoteBase(BaseModel):
    title: str
    content: str


class NoteInDB(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str    
