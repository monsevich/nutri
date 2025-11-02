from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient


router = Router()


@router.message(Command("report"))
@router.message(F.text == "Недельный отчёт")
async def show_report(message: Message) -> None:
    core_api_client: CoreApiClient = message.bot.get("core_api_client")
    try:
        data = await core_api_client.get_weekly_report(str(message.from_user.id))
    except Exception:
        await message.answer("Отчёт пока не готов. Собирай данные и возвращайся позже!")
        return

    flags = ", ".join(f"{key}: {value}" for key, value in data.get("status_flags", {}).items())
    text = f"Отчёт за неделю {data['week_start']} — {data['week_end']}\n\n{data['summary_text']}\n\nСтатус: {flags}"
    await message.answer(text)
