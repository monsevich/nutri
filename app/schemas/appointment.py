from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AppointmentBase(BaseModel):
    client_id: UUID
    staff_id: UUID
    service_id: UUID
    start_datetime: datetime
    status: str
    room: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentRead(AppointmentBase):
    id: UUID
    end_datetime: datetime

    class Config:
        orm_mode = True
