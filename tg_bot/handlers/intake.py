from datetime import date
from io import BytesIO
import logging
from typing import Any, Dict, Optional

import httpx

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient
from ..services.vision_api_client import VisionApiClient


router = Router()
logger = logging.getLogger(__name__)


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
    update_id = getattr(message, "update_id", None)
    telegram_id = str(message.from_user.id) if message.from_user else "unknown"
    logger.debug(
        "Handling meal photo update_id=%s message_id=%s user_id=%s",
        update_id,
        message.message_id,
        telegram_id,
    )

    status_message = await message.answer("Приняла фото, анализирую…")
    bot = message.bot
    photo = message.photo[-1]
    image_buffer = BytesIO()
    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, destination=image_buffer)
    except Exception:
        logger.exception(
            "Failed to download photo update_id=%s file_id=%s",
            update_id,
            photo.file_id,
        )
        await status_message.edit_text(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return
    image_buffer.seek(0)
    image_bytes = image_buffer.getvalue()
    logger.debug(
        "Downloaded photo for user_id=%s update_id=%s file_id=%s size=%sB",
        telegram_id,
        update_id,
        photo.file_id,
        len(image_bytes),
    )

    dispatcher = bot.dispatcher
    vision_client: VisionApiClient = dispatcher["vision_api_client"]
    core_api_client: CoreApiClient = dispatcher["core_api_client"]

    try:
        logger.debug(
            "Requesting vision estimate for update_id=%s file_id=%s",
            update_id,
            photo.file_id,
        )
        result = await vision_client.estimate_meal(
            image_bytes, filename=f"{photo.file_unique_id}.jpg"
        )
    except httpx.HTTPError:
        logger.exception(
            "Vision service request failed update_id=%s file_id=%s",
            update_id,
            photo.file_id,
        )
        await status_message.edit_text(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return

    label = result.get("label") or _format_label_from_candidates(result)
    calories_raw = result.get("calories_kcal")
    try:
        calories_number = float(calories_raw)
    except (TypeError, ValueError):
        calories_number = None

    logger.debug(
        "Vision response for user_id=%s: label=%s calories=%s raw=%s",
        telegram_id,
        label,
        calories_raw,
        result,
    )

    if calories_number is None:
        await status_message.edit_text(
            "Не получилось распознать блюдо, введите калории вручную."
        )
        return

    calories_text = _format_number(calories_number)
    label_text = label or "блюдо"

    payload = {
        "telegram_id": telegram_id,
        "date": date.today().isoformat(),
        "calories_in": calories_number,
    }
    logger.debug(
        "Sending daily intake to core_api for user_id=%s payload=%s",
        telegram_id,
        payload,
    )
    try:
        await core_api_client.log_daily_intake(payload)
    except httpx.HTTPError:
        logger.exception(
            "Failed to log intake to core update_id=%s payload=%s",
            update_id,
            payload,
        )
        await status_message.edit_text(
            (
                f"Оценила {label_text} в {calories_text} ккал, "
                "но не смогла записать в дневник, попробуй позже."
            )
        )
        return

    await status_message.edit_text(
        f"Записала: {calories_text} ккал из блюда «{label_text}»"
    )


def _format_label_from_candidates(result: Dict[str, Any]) -> Optional[str]:
    candidates = result.get("candidates")
    if not candidates:
        return None
    if isinstance(candidates, list):
        first = candidates[0]
        if isinstance(first, dict):
            return first.get("label") or first.get("title")
        if isinstance(first, str):
            return first
    return None
