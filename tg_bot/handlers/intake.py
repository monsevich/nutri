from datetime import date
from io import BytesIO

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient
from ..services.vision_api_client import VisionApiClient


router = Router()


class CaloriesState(StatesGroup):
    waiting_calories = State()


@router.message(Command("add_calories"))
@router.message(F.text == "Добавить калории")
async def request_calories(message: Message, state: FSMContext) -> None:
    await message.answer("Сколько калорий записать за сегодня? Укажите число в ккал.")
    await state.set_state(CaloriesState.waiting_calories)


@router.message(CaloriesState.waiting_calories)
async def process_manual_calories(message: Message, state: FSMContext) -> None:
    try:
        calories = float(message.text.replace(",", "."))
    except (AttributeError, ValueError):
        await message.answer("Нужно число, попробуй ещё раз.")
        return

    core_api_client: CoreApiClient = message.bot.get("core_api_client")
    await core_api_client.log_daily_intake(
        {
            "telegram_id": str(message.from_user.id),
            "date": date.today().isoformat(),
            "calories_in": calories,
        }
    )
    await message.answer(f"Записал {calories} ккал на сегодня.")
    await state.clear()


@router.message(F.photo)
async def handle_meal_photo(message: Message) -> None:
    photo = message.photo[-1]
    buffer = BytesIO()
    await message.bot.download(photo, destination=buffer)
    buffer.seek(0)

    vision_client: VisionApiClient = message.bot.get("vision_api_client")
    core_api_client: CoreApiClient = message.bot.get("core_api_client")

    try:
        result = await vision_client.estimate_meal(buffer.getvalue(), filename=f"{photo.file_unique_id}.jpg")
    except Exception:
        await message.answer("Не удалось распознать блюдо, попробуй позже.")
        return

    await core_api_client.log_daily_intake(
        {
            "telegram_id": str(message.from_user.id),
            "date": date.today().isoformat(),
            "calories_in": result["calories_kcal"],
        }
    )
    await message.answer(
        "Я записал приём пищи: ~{cal} ккал ({label}, {grams} г).".format(
            cal=result["calories_kcal"], label=result["label"], grams=result["portion_grams_est"]
        )
    )
