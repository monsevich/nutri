import json
from pathlib import Path
from typing import Dict

from .inference import classify


class NutritionService:
    def __init__(self, db_path: Path):
        self.db: Dict[str, Dict[str, float]] = json.loads(db_path.read_text(encoding="utf-8"))

    def estimate_portion_grams(self) -> int:
        return 200

    def calc_macros(self, label: str, portion_grams: int) -> Dict[str, float]:
        nutrition = self.db.get(label)
        if not nutrition:
            nutrition = next(iter(self.db.values()))
        factor = portion_grams / 100
        return {
            "calories_kcal": round(nutrition["calories_kcal"] * factor, 1),
            "proteins_g": round(nutrition["proteins_g"] * factor, 1),
            "fats_g": round(nutrition["fats_g"] * factor, 1),
            "carbs_g": round(nutrition["carbs_g"] * factor, 1),
        }


def estimate_meal(image_bytes: bytes, nutrition_service: NutritionService) -> Dict[str, float]:
    label, confidence = classify(image_bytes)
    portion_grams = nutrition_service.estimate_portion_grams()
    macros = nutrition_service.calc_macros(label, portion_grams)
    return {
        "label": label,
        "confidence": confidence,
        "portion_grams_est": portion_grams,
        **macros,
    }
