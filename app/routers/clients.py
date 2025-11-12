from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Client, User
from app.schemas.client import ClientCreate, ClientRead

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=List[ClientRead])
def list_clients(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    clients = (
        db.query(Client)
        .filter(Client.tenant_id == current_user.tenant_id)
        .order_by(Client.full_name)
        .all()
    )
    return clients


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(tenant_id=current_user.tenant_id, **payload.dict())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
