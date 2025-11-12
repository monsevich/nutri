from uuid import UUID
from pydantic import BaseModel


class TenantBase(BaseModel):
    name: str
    timezone: str
    plan: str
    is_active: bool = True


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: UUID

    class Config:
        orm_mode = True
