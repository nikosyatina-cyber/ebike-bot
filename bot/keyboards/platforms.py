from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import UserLevel

def get_platform_keyboard(user_level: UserLevel) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if user_level >= UserLevel.STAGER:
        builder.row(InlineKeyboardButton(text="🟡 Яндекс.Еда", callback_data="platform:yandex"))
        builder.row(InlineKeyboardButton(text="🔴 Достависта", callback_data="platform:dostavista"))
    if user_level >= UserLevel.BEGINNER:
        builder.row(InlineKeyboardButton(text="🟢 Х5", callback_data="platform:x5"))
        builder.row(InlineKeyboardButton(text="🟡 Магнит", callback_data="platform:magnit"))
    if user_level >= UserLevel.RACER:
        builder.row(InlineKeyboardButton(text="🔵 Озон Фреш", callback_data="platform:ozon"))
        builder.row(InlineKeyboardButton(text="🟣 WB Курьер", callback_data="platform:wb"))
    if user_level >= UserLevel.EXPERIENCED:
        builder.row(InlineKeyboardButton(text="🟠 TopGO", callback_data="platform:topgo"))
    if user_level >= UserLevel.ELITE:
        builder.row(InlineKeyboardButton(text="🟣 ВкусВилл", callback_data="platform:vkusvill"))
    if user_level >= UserLevel.LEGEND:
        builder.row(InlineKeyboardButton(text="🏴 Чёрный рынок", callback_data="platform:black_market"))
        builder.row(InlineKeyboardButton(text="👔 Элитные", callback_data="platform:elite"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()

def get_order_actions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Принять заказ", callback_data="order:accept"))
    builder.row(InlineKeyboardButton(text="🔄 Другие заказы", callback_data="order:refresh"))
    builder.row(InlineKeyboardButton(text="🔙 Сменить платформу", callback_data="back_to_platforms"))
    return builder.as_markup()

def get_ride_actions_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚴 Еду дальше", callback_data="ride:continue"))
    builder.row(InlineKeyboardButton(text="📋 Детали", callback_data="ride:details"))
    return builder.as_markup()