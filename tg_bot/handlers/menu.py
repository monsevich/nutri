from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient


router = Router()


def _format_menu(menu: dict) -> str:
    lines = ["Меню на неделю:"]
    for day, meals in menu.items():
        lines.append(f"\n{day}:")
        for meal_type, meal in meals.items():
            lines.append(f"  {meal_type.title()}: {meal['title']} (~{meal['calories_kcal']} ккал)")
    return "\n".join(lines)


@router.message(Command("menu"))
@router.message(F.text == "Меню на неделю")
async def show_menu(message: Message) -> None:
    dispatcher = message.bot.dispatcher
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    data = await core_api_client.get_week_menu(str(message.from_user.id))
    await message.answer(_format_menu(data["menu"]))
