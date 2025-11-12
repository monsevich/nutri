from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DealBase(BaseModel):
    client_id: UUID
    stage: str
    source: Optional[str] = None
    ai_summary: Optional[str] = None


class DealCreate(DealBase):
    pass


class DealRead(DealBase):
    id: UUID

    class Config:
        orm_mode = True
