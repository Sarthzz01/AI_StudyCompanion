from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: Optional[str] = "student"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserAuthResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    joined: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthResponse

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)

class PasswordResetResponse(BaseModel):
    message: str
    dev_reset_link: Optional[str] = None

