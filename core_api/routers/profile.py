from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..db import get_session
from ..schemas import ProfileInitRequest, ProfileInitResponse
from ..services.calorie_calc import calculate_daily_calories


router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/init", response_model=ProfileInitResponse)
async def init_profile(payload: ProfileInitRequest, session: AsyncSession = Depends(get_session)) -> ProfileInitResponse:
    result = await session.execute(
        select(models.User).where(models.User.telegram_id == payload.telegram_id)
    )
    user = result.scalars().first()

    if user is None:
        user = models.User(
            telegram_id=payload.telegram_id,
            age=payload.age,
            sex=payload.sex,
            height_cm=payload.height_cm,
            start_weight_kg=payload.weight_kg,
            target_weight_kg=payload.target_weight_kg,
            waist_cm=payload.waist_cm,
            hips_cm=payload.hips_cm,
            chest_cm=payload.chest_cm,
            chronic_conditions=payload.chronic_conditions or None,
            activity_level=payload.activity_level,
        )
        session.add(user)
    else:
        user.age = payload.age
        user.sex = payload.sex
        user.height_cm = payload.height_cm
        user.target_weight_kg = payload.target_weight_kg
        user.waist_cm = payload.waist_cm
        user.hips_cm = payload.hips_cm
        user.chest_cm = payload.chest_cm
        user.chronic_conditions = payload.chronic_conditions or None
        user.activity_level = payload.activity_level

    await session.commit()
    await session.refresh(user)

    calc_result = calculate_daily_calories(
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        age=payload.age,
        sex=payload.sex,
        activity_level=payload.activity_level,
        target_weight=payload.target_weight_kg,
    )

    medical_warning = bool(payload.chronic_conditions)
    return ProfileInitResponse(
        daily_calorie_target_kcal=calc_result.daily_target,
        medical_warning=medical_warning,
    )
