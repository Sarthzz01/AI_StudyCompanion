from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class ProfileOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: EmailStr
    role: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    joined: str
    preferences: Dict[str, Any] = {}

    class Config:
        from_attributes = True
