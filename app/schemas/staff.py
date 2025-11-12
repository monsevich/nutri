from typing import List
from uuid import UUID
from pydantic import BaseModel


class StaffBase(BaseModel):
    full_name: str
    role: str
    is_active: bool = True


class StaffCreate(StaffBase):
    service_ids: List[UUID] = []


class StaffRead(StaffBase):
    id: UUID
    service_ids: List[UUID] = []

    class Config:
        orm_mode = True
