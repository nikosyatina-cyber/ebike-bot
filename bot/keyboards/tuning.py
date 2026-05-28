from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tuning_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню тюнинга."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚡ Мотор-колесо", callback_data="tuning:motor"))
    builder.row(InlineKeyboardButton(text="🧠 Контроллер", callback_data="tuning:controller"))
    builder.row(InlineKeyboardButton(text="🔋 Аккумулятор", callback_data="tuning:battery"))
    builder.row(InlineKeyboardButton(text="🛞 Маятник", callback_data="tuning:pendulum"))
    builder.row(InlineKeyboardButton(text="🛑 Тормозная система", callback_data="tuning:brakes"))
    builder.row(InlineKeyboardButton(text="🎨 Внешний вид", callback_data="tuning:visual"))
    builder.row(InlineKeyboardButton(text="📊 Статус сборки", callback_data="tuning:status"))
    builder.row(InlineKeyboardButton(text="🔙 Назад в гараж", callback_data="back_to_garage"))
    return builder.as_markup()