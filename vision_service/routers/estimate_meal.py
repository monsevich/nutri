import logging

from fastapi import APIRouter, File, UploadFile, HTTPException

from ..service import NutritionService, estimate_meal


def get_router(nutrition_service: NutritionService) -> APIRouter:
    router = APIRouter(prefix="/vision", tags=["vision"])
    logger = logging.getLogger(__name__)

    @router.post("/estimate_meal")
    async def estimate_meal_endpoint(image: UploadFile = File(...)):
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")
        await image.seek(0)
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Файл изображения пустой")
        result = estimate_meal(image_bytes, nutrition_service)
        logger.info(
            "Vision estimate: size=%sB label=%s calories=%s",
            len(image_bytes),
            result.get("label"),
            result.get("calories_kcal"),
        )
        return result

    return router
