from uuid import UUID
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    tenant_id: UUID
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: UUID
    tenant_id: UUID
    email: EmailStr
