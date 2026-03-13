from datetime import datetime
from pydantic import BaseModel, EmailStr

from auth.models import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.employee
    department: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
