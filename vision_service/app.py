from pathlib import Path

from fastapi import FastAPI

from .routers.estimate_meal import get_router
from .service import NutritionService


nutrition_service = NutritionService(Path(__file__).parent / "nutrition_db.json")
app = FastAPI(title="Vision Service", description="Оценка блюд по фото")
app.include_router(get_router(nutrition_service))


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
