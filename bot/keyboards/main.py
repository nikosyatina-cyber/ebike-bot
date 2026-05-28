from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_confirm_cancel() -> InlineKeyboardMarkup:
    """Подтверждение / Отмена."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    builder.adjust(2)
    return builder.as_markup()


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура разделов FAQ."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Платформы", callback_data="faq:platforms"))
    builder.row(InlineKeyboardButton(text="🚲 Транспорт", callback_data="faq:transport"))
    builder.row(InlineKeyboardButton(text="⭐ Уровни и опыт", callback_data="faq:levels"))
    builder.row(InlineKeyboardButton(text="🎯 Навыки", callback_data="faq:skills"))
    builder.row(InlineKeyboardButton(text="📊 Рейтинг", callback_data="faq:rating"))
    builder.row(InlineKeyboardButton(text="🌍 Зоны и драки", callback_data="faq:zones"))
    builder.row(InlineKeyboardButton(text="👮 Патрули и штрафы", callback_data="faq:patrol"))
    builder.row(InlineKeyboardButton(text="🏆 Достижения", callback_data="faq:achievements"))
    builder.row(InlineKeyboardButton(text="💬 Команды", callback_data="faq:commands"))
    builder.row(InlineKeyboardButton(text="💰 Экономика", callback_data="faq:economy"))
    builder.row(InlineKeyboardButton(text="🔙 Закрыть", callback_data="faq:close"))
    builder.adjust(1)
    return builder.as_markup()