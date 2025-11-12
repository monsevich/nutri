from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Appointment, Client, Service, Staff, User
from app.models.appointment import APPOINTMENT_STATUSES
from app.schemas.appointment import AppointmentCreate, AppointmentRead

router = APIRouter(prefix="/appointments", tags=["appointments"])


def serialize_appointment(instance: Appointment) -> AppointmentRead:
    return AppointmentRead(
        id=instance.id,
        client_id=instance.client_id,
        staff_id=instance.staff_id,
        service_id=instance.service_id,
        start_datetime=instance.start_datetime,
        end_datetime=instance.end_datetime,
        status=instance.status,
        room=instance.room,
    )


@router.get("", response_model=List[AppointmentRead])
def list_appointments(
    date_filter: Optional[date] = Query(None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Appointment).filter(Appointment.tenant_id == current_user.tenant_id)
    if date_filter:
        day_start = datetime.combine(date_filter, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        query = query.filter(
            Appointment.start_datetime >= day_start,
            Appointment.start_datetime < day_end,
        )
    appointments = query.order_by(Appointment.start_datetime).all()
    return [serialize_appointment(item) for item in appointments]


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.status not in APPOINTMENT_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    client = db.query(Client).filter(Client.id == payload.client_id).first()
    staff_member = db.query(Staff).filter(Staff.id == payload.staff_id).first()
    service = db.query(Service).filter(Service.id == payload.service_id).first()

    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client not found")
    if not staff_member or staff_member.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Staff not found")
    if not service or service.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service not found")

    duration_minutes = int(service.duration_minutes)
    end_datetime = payload.start_datetime + timedelta(minutes=duration_minutes)

    appointment = Appointment(
        tenant_id=current_user.tenant_id,
        client_id=payload.client_id,
        staff_id=payload.staff_id,
        service_id=payload.service_id,
        start_datetime=payload.start_datetime,
        end_datetime=end_datetime,
        status=payload.status,
        room=payload.room,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return serialize_appointment(appointment)
