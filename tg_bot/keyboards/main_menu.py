from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мой прогресс"), KeyboardButton(text="Меню на неделю")],
        [KeyboardButton(text="Записать замеры"), KeyboardButton(text="Добавить калории")],
        [KeyboardButton(text="Недельный отчёт")],
        [KeyboardButton(text="Фото приёма пищи")],
    ],
    resize_keyboard=True,
)
