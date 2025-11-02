from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import MenuPlanResponse
from ..services.calorie_calc import calculate_daily_calories
from ..services.menu_generator import generate_week_menu


router = APIRouter(prefix="/menu", tags=["menu"])


async def _get_user(session: AsyncSession, telegram_id: str) -> models.User:
    result = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


def _current_week_range(today: date) -> tuple[date, date]:
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


@router.get("/week", response_model=MenuPlanResponse)
async def get_week_menu(telegram_id: str, session: AsyncSession = Depends(get_session)) -> MenuPlanResponse:
    user = await _get_user(session, telegram_id)
    today = date.today()
    week_start, week_end = _current_week_range(today)

    result = await session.execute(
        select(models.MenuPlan).where(models.MenuPlan.user_id == user.id, models.MenuPlan.week_start == week_start)
    )
    menu_plan = result.scalars().first()

    if menu_plan is None:
        weight_for_calc = user.start_weight_kg
        calorie_target = calculate_daily_calories(
            weight_kg=weight_for_calc,
            height_cm=user.height_cm,
            age=user.age,
            sex=user.sex,
            activity_level=user.activity_level,
            target_weight=user.target_weight_kg,
        ).daily_target
        generated_menu = generate_week_menu(week_start, calorie_target)
        menu_plan = models.MenuPlan(user_id=user.id, week_start=week_start, menu_json=generated_menu)
        session.add(menu_plan)
        await session.commit()
        await session.refresh(menu_plan)

    return MenuPlanResponse(week_start=menu_plan.week_start, week_end=week_end, menu=menu_plan.menu_json)
