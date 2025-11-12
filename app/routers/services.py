from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Service, User
from app.schemas.service import ServiceCreate, ServiceRead

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=List[ServiceRead])
def list_services(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    services = (
        db.query(Service)
        .filter(Service.tenant_id == current_user.tenant_id)
        .order_by(Service.name)
        .all()
    )
    return services


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = Service(tenant_id=current_user.tenant_id, **payload.dict())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service
