from fastapi import APIRouter, File, UploadFile, HTTPException

from ..service import NutritionService, estimate_meal


def get_router(nutrition_service: NutritionService) -> APIRouter:
    router = APIRouter(prefix="/vision", tags=["vision"])

    @router.post("/estimate_meal")
    async def estimate_meal_endpoint(image: UploadFile = File(...)):
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        image_bytes = await image.read()
        result = estimate_meal(image_bytes, nutrition_service)
        return result

    return router
