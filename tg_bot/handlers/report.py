from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient


router = Router()


@router.message(Command("report"))
@router.message(F.text == "Недельный отчёт")
async def show_report(message: Message) -> None:
    dispatcher = message.bot.dispatcher
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    try:
        data = await core_api_client.get_weekly_report(str(message.from_user.id))
    except Exception:
        await message.answer("Отчёт пока не готов. Собирай данные и возвращайся позже!")
        return

    lines = [
        f"Отчёт за неделю {data['week_start']} — {data['week_end']}",
        "",
        data.get("summary_text", "Данные за неделю пока пустые."),
    ]

    status_flags = data.get("status_flags") or {}
    if status_flags:
        flags_text = ", ".join(f"{key}: {value}" for key, value in status_flags.items())
        lines.extend(["", f"Статус: {flags_text}"])

    await message.answer("\n".join(lines))
