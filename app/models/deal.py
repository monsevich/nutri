import uuid
from sqlalchemy import Column, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base

DEAL_STAGES = ("new", "consultation", "booked", "done", "upsell")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    stage = Column(Enum(*DEAL_STAGES, name="deal_stage"), nullable=False)
    source = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)

    tenant = relationship("Tenant", backref="deals")
    client = relationship("Client", backref="deals")
