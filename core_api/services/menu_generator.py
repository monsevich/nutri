from datetime import date, timedelta
from typing import Dict


DEFAULT_MEALS = [
    "овсянка с ягодами",
    "гречка с курицей",
    "суп из овощей",
    "рыба с овощами",
    "творог с орехами",
    "паста болоньезе",
    "салат с киноа",
]


MEAL_STRUCTURE = ["завтрак", "обед", "ужин", "перекус"]


def generate_week_menu(week_start: date, daily_calories: int) -> Dict[str, Dict[str, Dict[str, int]]]:
    per_meal = int(daily_calories / len(MEAL_STRUCTURE))
    week_menu: Dict[str, Dict[str, Dict[str, int]]] = {}
    for i in range(7):
        day = week_start + timedelta(days=i)
        meals_for_day: Dict[str, Dict[str, int]] = {}
        for idx, meal_type in enumerate(MEAL_STRUCTURE):
            meal_name = DEFAULT_MEALS[(i + idx) % len(DEFAULT_MEALS)]
            meals_for_day[meal_type] = {
                "title": meal_name,
                "calories_kcal": per_meal,
            }
        week_menu[day.isoformat()] = meals_for_day
    return week_menu
