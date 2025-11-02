from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ProfileInitRequest(BaseModel):
    telegram_id: str
    age: int
    sex: str
    height_cm: float
    weight_kg: float
    target_weight_kg: float
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    chest_cm: Optional[float] = None
    chronic_conditions: List[str] = Field(default_factory=list)
    activity_level: str


class ProfileInitResponse(BaseModel):
    daily_calorie_target_kcal: int
    medical_warning: bool


class DailyIntakeLogRequest(BaseModel):
    telegram_id: str
    date: date
    calories_in: float


class BodyLogRequest(BaseModel):
    telegram_id: str
    date: date
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None
    hips_cm: Optional[float] = None
    chest_cm: Optional[float] = None


class ProgressSummary(BaseModel):
    last_weight_kg: Optional[float]
    last_waist_cm: Optional[float]
    last_hips_cm: Optional[float]
    last_chest_cm: Optional[float]
    avg_calories_last_7_days: Optional[float]
    message: str


class MenuPlanResponse(BaseModel):
    week_start: date
    week_end: date
    menu: dict


class WeeklyReportResponse(BaseModel):
    week_start: date
    week_end: date
    summary_text: str
    status_flags: dict
