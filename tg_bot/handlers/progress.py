from aiogram import Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient


router = Router()


async def _format_progress(data: dict) -> str:
    lines = ["Последний прогресс:"]
    if data.get("last_weight_kg") is not None:
        lines.append(f"Вес: {data['last_weight_kg']} кг")
    if data.get("last_waist_cm") is not None:
        lines.append(f"Талия: {data['last_waist_cm']} см")
    if data.get("last_hips_cm") is not None:
        lines.append(f"Бёдра: {data['last_hips_cm']} см")
    if data.get("last_chest_cm") is not None:
        lines.append(f"Грудь: {data['last_chest_cm']} см")
    if data.get("avg_calories_last_7_days") is not None:
        lines.append(f"Средние калории за 7 дней: {data['avg_calories_last_7_days']} ккал")
    lines.append(data.get("message", ""))
    return "\n".join(lines)


@router.message(Command("progress"))
@router.message(F.text == "Мой прогресс")
async def show_progress(message: Message) -> None:
    dispatcher = Dispatcher.get_current()
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    data = await core_api_client.get_progress_summary(str(message.from_user.id))
    await message.answer(_format_progress(data))
