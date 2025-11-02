from datetime import date
from statistics import mean
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DailyLog, WeeklyReport
from .calorie_calc import calculate_daily_calories


def _calc_change(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return round(values[-1] - values[0], 1)


async def fetch_logs_for_period(session: AsyncSession, user_id: int, start: date, end: date) -> List[DailyLog]:
    result = await session.execute(
        select(DailyLog)
        .where(DailyLog.user_id == user_id)
        .where(DailyLog.date >= start)
        .where(DailyLog.date <= end)
        .order_by(DailyLog.date)
    )
    return list(result.scalars().all())


async def generate_weekly_report(session: AsyncSession, user, week_start: date, week_end: date) -> WeeklyReport:
    logs = await fetch_logs_for_period(session, user.id, week_start, week_end)
    calorie_values = [log.calories_in for log in logs if log.calories_in is not None]
    avg_calories = round(mean(calorie_values), 1) if calorie_values else None
    weight_values = [log.weight_kg for log in logs if log.weight_kg is not None]
    waist_values = [log.waist_cm for log in logs if log.waist_cm is not None]

    latest_weight = weight_values[-1] if weight_values else user.start_weight_kg
    calorie_target = calculate_daily_calories(
        weight_kg=latest_weight,
        height_cm=user.height_cm,
        age=user.age,
        sex=user.sex,
        activity_level=user.activity_level,
        target_weight=user.target_weight_kg,
    ).daily_target

    activity_flags = [log.activity_level for log in logs if log.activity_level]
    low_activity_ratio = 0
    if activity_flags:
        low_count = sum(1 for level in activity_flags if level == "low")
        low_activity_ratio = low_count / len(activity_flags)

    status_flags: Dict[str, bool | str | float] = {}
    if avg_calories is not None:
        status_flags["avg_calories"] = avg_calories
        status_flags["calorie_delta"] = round(avg_calories - calorie_target, 1)
    weight_change = _calc_change(weight_values)
    waist_change = _calc_change(waist_values)
    if weight_change is not None:
        status_flags["weight_change"] = weight_change
    if waist_change is not None:
        status_flags["waist_change"] = waist_change
    if low_activity_ratio >= 0.6:
        status_flags["low_activity"] = True

    summary_parts = [
        "Отчёт за неделю готов!",
        f"Цель по калориям: ~{calorie_target} ккал/сутки.",
    ]
    if avg_calories is not None:
        summary_parts.append(f"Среднее потребление: {avg_calories} ккал.")
        delta = avg_calories - calorie_target
        if abs(delta) < 100:
            summary_parts.append("Ты держишься рядом с целью — супер!")
        elif delta > 0:
            summary_parts.append("Есть перебор по калориям, попробуй немного сократить порции.")
        else:
            summary_parts.append("Небольшой недобор по калориям, следи за самочувствием.")
    if weight_change is not None:
        summary_parts.append(f"Изменение веса: {weight_change:+} кг.")
    if waist_change is not None:
        summary_parts.append(f"Изменение талии: {waist_change:+} см.")
    if status_flags.get("low_activity"):
        summary_parts.append("Замечена низкая активность — постарайся добавить прогулки или зарядку.")

    summary_text = " ".join(summary_parts)

    report = WeeklyReport(
        user_id=user.id,
        week_start=week_start,
        week_end=week_end,
        summary_text=summary_text,
        status_flags=status_flags,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report
