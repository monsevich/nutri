from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import WeeklyReportResponse


router = APIRouter(prefix="/report", tags=["report"])


async def _get_user(session: AsyncSession, telegram_id: str) -> models.User:
    result = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


def _empty_report_response() -> WeeklyReportResponse:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return WeeklyReportResponse(
        week_start=week_start,
        week_end=week_end,
        summary_text="Данные за неделю пока пустые.",
        status_flags={},
    )


@router.get("/weekly", response_model=WeeklyReportResponse)
async def get_weekly_report(telegram_id: str, session: AsyncSession = Depends(get_session)) -> WeeklyReportResponse:
    try:
        user = await _get_user(session, telegram_id)
    except HTTPException as exc:
        if exc.status_code == 404:
            return _empty_report_response()
        raise

    result = await session.execute(
        select(models.WeeklyReport)
        .where(models.WeeklyReport.user_id == user.id)
        .order_by(models.WeeklyReport.week_start.desc())
    )
    report = result.scalars().first()
    if not report:
        return _empty_report_response()

    return WeeklyReportResponse(
        week_start=report.week_start,
        week_end=report.week_end,
        summary_text=report.summary_text,
        status_flags=report.status_flags,
    )
