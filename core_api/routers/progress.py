from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import ProgressSummary
from ..services.calorie_calc import calculate_daily_calories


router = APIRouter(prefix="/progress", tags=["progress"])


async def _get_user(session: AsyncSession, telegram_id: str) -> models.User:
    result = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@router.get("/summary", response_model=ProgressSummary)
async def progress_summary(telegram_id: str, session: AsyncSession = Depends(get_session)) -> ProgressSummary:
    user = await _get_user(session, telegram_id)
    today = date.today()
    week_start = today - timedelta(days=6)

    logs_result = await session.execute(
        select(models.DailyLog)
        .where(models.DailyLog.user_id == user.id)
        .where(models.DailyLog.date >= week_start)
        .order_by(models.DailyLog.date)
    )
    logs = logs_result.scalars().all()

    last_log = logs[-1] if logs else None
    if not last_log:
        latest_log_result = await session.execute(
            select(models.DailyLog)
            .where(models.DailyLog.user_id == user.id)
            .order_by(models.DailyLog.date.desc())
        )
        last_log = latest_log_result.scalars().first()

    avg_calories = None
    calorie_values = [log.calories_in for log in logs if log.calories_in is not None]
    if calorie_values:
        avg_calories = round(sum(calorie_values) / len(calorie_values), 1)

    weight_for_calc = last_log.weight_kg if last_log and last_log.weight_kg else user.start_weight_kg
    target_calories = calculate_daily_calories(
        weight_kg=weight_for_calc,
        height_cm=user.height_cm,
        age=user.age,
        sex=user.sex,
        activity_level=user.activity_level,
        target_weight=user.target_weight_kg,
    ).daily_target

    message = ""
    if avg_calories is None:
        message = "Данных за последние дни мало, продолжай вести дневник."
    else:
        delta = avg_calories - target_calories
        if abs(delta) < 100:
            message = "Ты держишься около цели. Так держать!"
        elif delta > 0:
            message = "Есть перебор по калориям, попробуй скорректировать рацион."
        else:
            message = "Небольшой недобор калорий, следи за самочувствием."

    return ProgressSummary(
        last_weight_kg=last_log.weight_kg if last_log else None,
        last_waist_cm=last_log.waist_cm if last_log else None,
        last_hips_cm=last_log.hips_cm if last_log else None,
        last_chest_cm=last_log.chest_cm if last_log else None,
        avg_calories_last_7_days=avg_calories,
        message=message,
    )
