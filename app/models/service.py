import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Numeric, nullable=False)
    is_medical = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    tenant = relationship("Tenant", backref="services")
    staff_members = relationship(
        "Staff",
        secondary="staff_services",
        back_populates="services",
    )
