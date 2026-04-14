from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entities import Role


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=140)
    phone: str = Field(min_length=6, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.driver


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: str
    role: Role
