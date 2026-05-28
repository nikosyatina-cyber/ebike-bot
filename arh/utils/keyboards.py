# bot/utils/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="🏆 Топ"),
        KeyboardButton(text="⭐ Карма"),
        KeyboardButton(text="🛒 Поиск"),
        KeyboardButton(text="🔔 Мои алерты")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_marketplace_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора маркетплейса"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 Ozon", callback_data="market_ozon")
    builder.button(text="🟣 Wildberries", callback_data="market_wb")
    builder.button(text="🌐 Все", callback_data="market_all")
    builder.adjust(3)
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура отмены"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)