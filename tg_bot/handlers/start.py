from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..keyboards.main_menu import main_menu
from ..services.core_api_client import CoreApiClient


router = Router()


class ProfileState(StatesGroup):
    age = State()
    sex = State()
    height = State()
    weight = State()
    target_weight = State()
    waist = State()
    hips = State()
    chest = State()
    chronic = State()
    activity = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    disclaimer = (
        "Привет! Я бот-нутрициолог. Я не врач, и мои рекомендации не заменяют консультацию специалиста."
    )
    await message.answer(disclaimer)
    await message.answer("Сколько вам лет?")
    await state.set_state(ProfileState.age)


@router.message(ProfileState.age)
async def process_age(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("Введите возраст числом.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Укажите пол (м/ж).")
    await state.set_state(ProfileState.sex)


@router.message(ProfileState.sex)
async def process_sex(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Введите пол (м/ж).")
        return
    sex = message.text.lower()
    if sex not in {"м", "ж", "m", "f", "male", "female"}:
        await message.answer("Используйте формат м/ж.")
        return
    normalized_sex = {
        "м": "male",
        "m": "male",
        "male": "male",
        "ж": "female",
        "f": "female",
        "female": "female",
    }[sex]
    await state.update_data(sex=normalized_sex)
    await message.answer("Введите рост в сантиметрах.")
    await state.set_state(ProfileState.height)


@router.message(ProfileState.height)
async def process_height(message: Message, state: FSMContext) -> None:
    try:
        height = float(message.text.replace(",", "."))
    except (TypeError, ValueError):
        await message.answer("Введите рост числом.")
        return
    await state.update_data(height=height)
    await message.answer("Введите текущий вес в килограммах.")
    await state.set_state(ProfileState.weight)


@router.message(ProfileState.weight)
async def process_weight(message: Message, state: FSMContext) -> None:
    try:
        weight = float(message.text.replace(",", "."))
    except (TypeError, ValueError):
        await message.answer("Введите вес числом.")
        return
    await state.update_data(weight=weight)
    await message.answer("Введите целевой вес в килограммах.")
    await state.set_state(ProfileState.target_weight)


@router.message(ProfileState.target_weight)
async def process_target_weight(message: Message, state: FSMContext) -> None:
    try:
        target_weight = float(message.text.replace(",", "."))
    except (TypeError, ValueError):
        await message.answer("Введите целевой вес числом.")
        return
    await state.update_data(target_weight=target_weight)
    await message.answer("Обхват талии в сантиметрах (если не хотите отвечать, напишите 0).")
    await state.set_state(ProfileState.waist)


def _parse_float(value: str) -> float | None:
    try:
        number = float(value.replace(",", "."))
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


@router.message(ProfileState.waist)
async def process_waist(message: Message, state: FSMContext) -> None:
    waist = _parse_float(message.text or "")
    await state.update_data(waist=waist)
    await message.answer("Обхват бёдер в сантиметрах (0, если пропустить).")
    await state.set_state(ProfileState.hips)


@router.message(ProfileState.hips)
async def process_hips(message: Message, state: FSMContext) -> None:
    hips = _parse_float(message.text or "")
    await state.update_data(hips=hips)
    await message.answer("Обхват груди в сантиметрах (0, если пропустить).")
    await state.set_state(ProfileState.chest)


@router.message(ProfileState.chest)
async def process_chest(message: Message, state: FSMContext) -> None:
    chest = _parse_float(message.text or "")
    await state.update_data(chest=chest)
    await message.answer(
        "Есть ли хронические состояния? Укажите через запятую или напишите 'нет'."
    )
    await state.set_state(ProfileState.chronic)


@router.message(ProfileState.chronic)
async def process_chronic(message: Message, state: FSMContext) -> None:
    chronic_text = (message.text or "").strip().lower()
    chronic = []
    if chronic_text and chronic_text not in {"нет", "no"}:
        chronic = [item.strip() for item in chronic_text.split(",") if item.strip()]
    await state.update_data(chronic=chronic)
    await message.answer(
        "Выберите уровень активности: low / moderate / high. Можно написать словами."
    )
    await state.set_state(ProfileState.activity)


@router.message(ProfileState.activity)
async def process_activity(message: Message, state: FSMContext) -> None:
    activity = (message.text or "low").strip().lower()
    if activity not in {"low", "moderate", "high", "very_high", "высокая", "низкая", "средняя"}:
        await message.answer("Используйте low / moderate / high.")
        return
    normalized_activity = {
        "низкая": "low",
        "средняя": "moderate",
        "высокая": "high",
    }.get(activity, activity)
    await state.update_data(activity=normalized_activity)

    data = await state.get_data()
    dispatcher = message.bot.dispatcher
    core_api_client: CoreApiClient = dispatcher["core_api_client"]
    payload = {
        "telegram_id": str(message.from_user.id),
        "age": data["age"],
        "sex": data["sex"],
        "height_cm": data["height"],
        "weight_kg": data["weight"],
        "target_weight_kg": data["target_weight"],
        "waist_cm": data.get("waist"),
        "hips_cm": data.get("hips"),
        "chest_cm": data.get("chest"),
        "chronic_conditions": data.get("chronic", []),
        "activity_level": normalized_activity,
    }
    response = await core_api_client.init_profile(payload)

    message_lines = [
        f"Твоя ориентировочная дневная норма: {response['daily_calorie_target_kcal']} ккал.",
    ]
    if response.get("medical_warning"):
        message_lines.append(
            "У тебя указаны хронические состояния — обязательно советуйся с врачом."
        )
    await message.answer("\n".join(message_lines), reply_markup=main_menu)
    await state.clear()
