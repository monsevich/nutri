from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Service, Staff, User
from app.schemas.staff import StaffCreate, StaffRead

router = APIRouter(prefix="/staff", tags=["staff"])


def serialize_staff(member: Staff) -> StaffRead:
    return StaffRead(
        id=member.id,
        full_name=member.full_name,
        role=member.role,
        is_active=member.is_active,
        service_ids=[service.id for service in member.services],
    )


@router.get("", response_model=List[StaffRead])
def list_staff(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    staff_members = (
        db.query(Staff)
        .filter(Staff.tenant_id == current_user.tenant_id)
        .order_by(Staff.full_name)
        .all()
    )
    return [serialize_staff(member) for member in staff_members]


@router.post("", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    services: List[Service] = []
    if payload.service_ids:
        services = (
            db.query(Service)
            .filter(
                Service.id.in_(payload.service_ids),
                Service.tenant_id == current_user.tenant_id,
            )
            .all()
        )
        if len(services) != len(set(payload.service_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Some services not found for tenant",
            )

    staff_member = Staff(
        tenant_id=current_user.tenant_id,
        full_name=payload.full_name,
        role=payload.role,
        is_active=payload.is_active,
        services=services,
    )
    db.add(staff_member)
    db.commit()
    db.refresh(staff_member)
    return serialize_staff(staff_member)
