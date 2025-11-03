import asyncio
import logging
import os
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from .handlers import body, intake, menu, progress, report, start
from .services.core_api_client import CoreApiClient
from .services.vision_api_client import VisionApiClient


logging.basicConfig(level=logging.INFO)


def load_settings() -> Dict[str, Any]:
    load_dotenv()
    settings = {
        "token": os.getenv("TG_BOT_TOKEN"),
        "core_api_url": os.getenv("CORE_API_URL"),
        "vision_api_url": os.getenv("VISION_API_URL"),
    }
    missing = [key for key, value in settings.items() if not value]
    if missing:
        raise RuntimeError(
            "Не заданы переменные окружения: " + ", ".join(sorted(missing))
        )
    return settings


async def main() -> None:
    settings = load_settings()

    bot = Bot(settings["token"], parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    core_api_client = CoreApiClient(settings["core_api_url"])
    vision_api_client = VisionApiClient(settings["vision_api_url"])

    dp["core_api_client"] = core_api_client
    dp["vision_api_client"] = vision_api_client

    dp.include_router(start.router)
    dp.include_router(progress.router)
    dp.include_router(menu.router)
    dp.include_router(report.router)
    dp.include_router(body.router)
    dp.include_router(intake.router)

    try:
        await dp.start_polling(bot)
    finally:
        await core_api_client.aclose()
        await vision_api_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
