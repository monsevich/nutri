from dataclasses import dataclass


_ACTIVITY_MULTIPLIERS = {
    "low": 1.2,
    "moderate": 1.55,
    "high": 1.725,
    "very_high": 1.9,
}


@dataclass
class CalorieCalculationResult:
    bmr: float
    tdee: float
    daily_target: int


def calculate_bmr_mifflin_st_jeor(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    sex = sex.lower()
    if sex in {"male", "m"}:
        s = 5
    elif sex in {"female", "f"}:
        s = -161
    else:
        s = 0
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + s


def activity_multiplier(level: str) -> float:
    return _ACTIVITY_MULTIPLIERS.get(level, 1.2)


def apply_goal_adjustment(tdee: float, current_weight: float, target_weight: float) -> float:
    if target_weight < current_weight:
        return tdee * 0.85
    if target_weight > current_weight:
        return tdee * 1.1
    return tdee


def calculate_daily_calories(weight_kg: float, height_cm: float, age: int, sex: str, activity_level: str, target_weight: float) -> CalorieCalculationResult:
    bmr = calculate_bmr_mifflin_st_jeor(weight_kg, height_cm, age, sex)
    tdee = bmr * activity_multiplier(activity_level)
    daily_target = apply_goal_adjustment(tdee, weight_kg, target_weight)
    return CalorieCalculationResult(bmr=bmr, tdee=tdee, daily_target=int(daily_target))
