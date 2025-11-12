from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class ClientBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    comment: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    id: UUID

    class Config:
        orm_mode = True
