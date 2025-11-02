from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import BodyLogRequest, DailyIntakeLogRequest


router = APIRouter(prefix="/log", tags=["log"])


async def _get_user(session: AsyncSession, telegram_id: str) -> models.User:
    result = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


async def _get_or_create_daily_log(session: AsyncSession, user_id: int, log_date: date) -> models.DailyLog:
    result = await session.execute(
        select(models.DailyLog).where(models.DailyLog.user_id == user_id, models.DailyLog.date == log_date)
    )
    daily_log = result.scalars().first()
    if daily_log is None:
        daily_log = models.DailyLog(user_id=user_id, date=log_date)
        session.add(daily_log)
    return daily_log


@router.post("/daily-intake")
async def log_daily_intake(payload: DailyIntakeLogRequest, session: AsyncSession = Depends(get_session)) -> dict:
    user = await _get_user(session, payload.telegram_id)
    daily_log = await _get_or_create_daily_log(session, user.id, payload.date)
    daily_log.calories_in = payload.calories_in
    await session.commit()
    return {"status": "ok"}


@router.post("/body")
async def log_body_metrics(payload: BodyLogRequest, session: AsyncSession = Depends(get_session)) -> dict:
    user = await _get_user(session, payload.telegram_id)
    daily_log = await _get_or_create_daily_log(session, user.id, payload.date)
    if payload.weight_kg is not None:
        daily_log.weight_kg = payload.weight_kg
    if payload.waist_cm is not None:
        daily_log.waist_cm = payload.waist_cm
    if payload.hips_cm is not None:
        daily_log.hips_cm = payload.hips_cm
    if payload.chest_cm is not None:
        daily_log.chest_cm = payload.chest_cm
    await session.commit()
    return {"status": "ok"}
