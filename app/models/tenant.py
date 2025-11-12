import uuid
from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    timezone = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
