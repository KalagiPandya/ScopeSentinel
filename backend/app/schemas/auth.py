from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.developer


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    role: str


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}
