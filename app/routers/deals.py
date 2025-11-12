from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models import Client, Deal, User
from app.models.deal import DEAL_STAGES
from app.schemas.deal import DealCreate, DealRead

router = APIRouter(prefix="/deals", tags=["deals"])


def serialize_deal(instance: Deal) -> DealRead:
    return DealRead(
        id=instance.id,
        client_id=instance.client_id,
        stage=instance.stage,
        source=instance.source,
        ai_summary=instance.ai_summary,
    )


@router.get("", response_model=List[DealRead])
def list_deals(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    deals = (
        db.query(Deal)
        .filter(Deal.tenant_id == current_user.tenant_id)
        .order_by(Deal.stage)
        .all()
    )
    return [serialize_deal(deal) for deal in deals]


@router.post("", response_model=DealRead, status_code=status.HTTP_201_CREATED)
def create_deal(
    payload: DealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.stage not in DEAL_STAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stage")

    client = db.query(Client).filter(Client.id == payload.client_id).first()
    if not client or client.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Client not found")

    deal = Deal(
        tenant_id=current_user.tenant_id,
        client_id=payload.client_id,
        stage=payload.stage,
        source=payload.source,
        ai_summary=payload.ai_summary,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return serialize_deal(deal)
