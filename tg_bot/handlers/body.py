from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..services.core_api_client import CoreApiClient


_MAIN_MENU_BUTTONS = {
    "Мой прогресс",
    "Меню на неделю",
    "Записать замеры",
    "Добавить калории",
    "Недельный отчёт",
    "Фото приёма пищи",
}


router = Router()


class BodyState(StatesGroup):
    weight = State()
    waist = State()
    hips = State()
    chest = State()


def _parse_optional_float(text: str) -> float | None:
    text = text.strip()
    if not text or text.lower() in {"нет", "-", "0"}:
        return None
    return float(text.replace(",", "."))


@router.message(Command("body"))
@router.message(F.text == "Записать замеры")
async def start_body_log(message: Message, state: FSMContext) -> None:
    await message.answer("Введите текущий вес в кг.")
    await state.set_state(BodyState.weight)


@router.message(BodyState.weight)
async def process_body_weight(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in _MAIN_MENU_BUTTONS:
        return

    try:
        weight = float(text.replace(",", "."))
    except (AttributeError, ValueError):
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    await state.update_data(weight=weight)
    await message.answer("Обхват талии (см). Если пропустить — напиши 0.")
    await state.set_state(BodyState.waist)


@router.message(BodyState.waist)
async def process_body_waist(message: Message, state: FSMContext) -> None:
    try:
        waist = _parse_optional_float(message.text or "")
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    await state.update_data(waist=waist)
    await message.answer("Обхват бёдер (см). 0 — пропустить.")
    await state.set_state(BodyState.hips)


@router.message(BodyState.hips)
async def process_body_hips(message: Message, state: FSMContext) -> None:
    try:
        hips = _parse_optional_float(message.text or "")
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    await state.update_data(hips=hips)
    await message.answer("Обхват груди (см). 0 — пропустить.")
    await state.set_state(BodyState.chest)


@router.message(BodyState.chest)
async def process_body_chest(message: Message, state: FSMContext) -> None:
    try:
        chest = _parse_optional_float(message.text or "")
    except ValueError:
        await message.answer("Нужно число. Попробуй ещё раз.")
        return
    data = await state.get_data()
    await state.clear()

    dispatcher = message.bot.dispatcher
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    await core_api_client.log_body(
        {
            "telegram_id": str(message.from_user.id),
            "date": date.today().isoformat(),
            "weight_kg": data.get("weight"),
            "waist_cm": data.get("waist"),
            "hips_cm": data.get("hips"),
            "chest_cm": chest,
        }
    )
    await message.answer("Записал замеры. Продолжай наблюдать за динамикой!")
