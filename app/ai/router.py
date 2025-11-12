from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/ai", tags=["ai"])


class AiRouteRequest(BaseModel):
    tenant_id: UUID
    message: str
    client_id: Optional[UUID] = None


class AiRouteResponse(BaseModel):
    intent: str
    suggestions: List[str]


BOOK_KEYWORDS = {"book", "appointment", "запис", "schedule"}


@router.post("/route", response_model=AiRouteResponse)
def route_message(payload: AiRouteRequest) -> AiRouteResponse:
    lowered = payload.message.lower()
    if any(keyword in lowered for keyword in BOOK_KEYWORDS):
        return AiRouteResponse(intent="book_appointment", suggestions=["create_appointment"])
    return AiRouteResponse(intent="answer_from_kb", suggestions=["search_kb"])
