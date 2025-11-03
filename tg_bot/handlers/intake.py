from datetime import date
from io import BytesIO

import httpx

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

    dispatcher = message.bot.dispatcher
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    payload = {
        "telegram_id": str(message.from_user.id),
        "date": date.today().isoformat(),
        "calories_in": calories,
    }
    try:
        await core_api_client.log_daily_intake(payload)
    except httpx.HTTPError:
        await message.answer("Не удалось сохранить данные, попробуйте ещё раз позже.")
        return
    await message.answer(
        f"Записала: {_format_number(calories)} ккал на сегодня. Смотреть в “Мой прогресс”."
    )
    await state.clear()


@router.message(F.text == "Фото приёма пищи")
async def request_meal_photo(message: Message) -> None:
    await message.answer("Отправьте фото блюда, я попробую оценить калорийность.")


def _format_number(value: float) -> str:
    return format(value, ".10g")


@router.message(F.photo)
async def handle_meal_photo(message: Message) -> None:
    bot = message.bot
    photo = message.photo[-1]
    try:
        file = await bot.get_file(photo.file_id)
        buffer = BytesIO()
        await bot.download_file(file.file_path, destination=buffer)
    except Exception:
        await message.answer(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return
    buffer.seek(0)

    dispatcher = bot.dispatcher
    vision_client: VisionApiClient = dispatcher["vision_api_client"]
    core_api_client: CoreApiClient = dispatcher["core_api_client"]

    try:
        result = await vision_client.estimate_meal(
            buffer.getvalue(), filename=f"{photo.file_unique_id}.jpg"
        )
    except httpx.HTTPError:
        await message.answer(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return

    calories = result.get("calories_kcal")
    label = result.get("label")
    if calories is None or label is None:
        await message.answer(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return

    await message.answer(
        f"Похоже, это: {label}. Калорийность: {_format_number(calories)} ккал."
    )

    payload = {
        "telegram_id": str(message.from_user.id),
        "date": date.today().isoformat(),
        "calories_in": calories,
    }
    try:
        await core_api_client.log_daily_intake(payload)
    except httpx.HTTPError:
        await message.answer(
            "Не удалось сохранить данные, введите калории вручную."
        )
        return

    await message.answer(
        f"Записала: {_format_number(calories)} ккал на сегодня. Смотреть в “Мой прогресс”."
    )
