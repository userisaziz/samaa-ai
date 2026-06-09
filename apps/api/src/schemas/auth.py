import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    brand_id: uuid.UUID | None = None
    store_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class LoginResponse(TokenResponse):
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str
