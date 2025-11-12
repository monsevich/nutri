from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ServiceBase(BaseModel):
    name: str
    duration_minutes: int
    price: Decimal
    is_medical: bool = False
    description: Optional[str] = None


class ServiceCreate(ServiceBase):
    pass


class ServiceRead(ServiceBase):
    id: UUID

    class Config:
        orm_mode = True
