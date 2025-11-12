import uuid
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

APPOINTMENT_STATUSES = ("planned", "confirmed", "done", "canceled")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(*APPOINTMENT_STATUSES, name="appointment_status"), nullable=False)
    room = Column(String, nullable=True)

    tenant = relationship("Tenant", backref="appointments")
    client = relationship("Client", backref="appointments")
    staff = relationship("Staff", backref="appointments")
    service = relationship("Service", backref="appointments")
