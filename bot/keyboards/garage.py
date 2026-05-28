from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_garage_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔧 Обслуживание", callback_data="garage:service"))
    builder.row(InlineKeyboardButton(text="🔧 Тюнинг U2-U7", callback_data="garage:tuning"))
    builder.row(InlineKeyboardButton(text="🛒 Магазин расходников", callback_data="garage:shop"))
    builder.row(InlineKeyboardButton(text="🚲 Сменить транспорт", callback_data="garage:transport_select"))
    builder.row(InlineKeyboardButton(text="🔙 Выйти", callback_data="back_to_menu"))
    return builder.as_markup()

def get_service_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔍 Осмотр (100₽)", callback_data="service:inspect"))
    builder.row(InlineKeyboardButton(text="🔧 Профилактика (600₽)", callback_data="service:maintenance"))
    builder.row(InlineKeyboardButton(text="🛠 Капремонт (1800₽)", callback_data="service:overhaul"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_garage"))
    return builder.as_markup()

def get_shop_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    items = [("🧴 Смазка цепи — 150₽", "shop:lube"), ("🩹 Ремкомплект — 200₽", "shop:repair_kit"), ("🛑 Тормозные колодки — 350₽", "shop:brake_pads"), ("🔋 Запасной аккумулятор — 800₽", "shop:spare_battery"), ("🍔 Ланч-бокс — 250₽", "shop:lunchbox"), ("⚡ Энергетик — 150₽", "shop:energy"), ("🧥 Дождевик — 400₽", "shop:raincoat"), ("🧤 Термоперчатки — 300₽", "shop:gloves"), ("📱 Повербанк — 500₽", "shop:powerbank")]
    for name, cb in items:
        builder.row(InlineKeyboardButton(text=name, callback_data=cb))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_garage"))
    return builder.as_markup()


def get_transport_select_keyboard(user_level) -> InlineKeyboardMarkup:
    """Выбор транспорта."""
    from database.models import UserLevel

    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(
        text="🔧 Тюнинг U2-U7",
        callback_data="garage:tuning",
    ))

    builder.row(InlineKeyboardButton(
        text="🟤 Механический велосипед (бесплатно)",
        callback_data="transport:mechanic",
    ))

    if user_level >= UserLevel.STAGER:
        builder.row(InlineKeyboardButton(
            text="🟡 Яндекс Самокат (1₽/мин, 20 км, IOT)",
            callback_data="transport:yandex_scooter",
        ))

    if user_level >= UserLevel.ELITE:
        builder.row(InlineKeyboardButton(
            text="🟣 Яндекс Байк (1₽/нед, 40 км, IOT)",
            callback_data="transport:yandex_bike",
        ))

    # Wenbox с IOT (ур. 3)
    if user_level >= UserLevel.RACER:
        builder.row(InlineKeyboardButton(
            text="🔵 Аренда Wenbox IOT (500₽/день, 25 км/ч, 45 км)",
            callback_data="transport:wenbox_rent_iot",
        ))

    # Wenbox без IOT (ур. 5)
    if user_level >= UserLevel.ELITE:
        builder.row(InlineKeyboardButton(
            text="🔵 Аренда Wenbox без IOT (500₽/день, 45 км/ч, 40 км)",
            callback_data="transport:wenbox_rent",
        ))

    # Покупка Wenbox (ур. 4)
    if user_level >= UserLevel.EXPERIENCED:
        builder.row(InlineKeyboardButton(
            text="🟢 Купить Wenbox (35 000₽, 50 км/ч, 45 км)",
            callback_data="transport:wenbox_buy",
        ))

    # U2-U7 с IOT (ур. 5)
    if user_level >= UserLevel.ELITE:
        builder.row(InlineKeyboardButton(
            text="🔴 Аренда U2-U7 IOT (900₽/день, 25 км/ч, 80 км)",
            callback_data="transport:u2u7_rent_iot",
        ))

    # U2-U7 без IOT (ур. 7)
    if user_level >= UserLevel.LEGEND:
        builder.row(InlineKeyboardButton(
            text="🔴 Аренда U2-U7 без IOT (900₽/день, 60 км/ч, 70 км)",
            callback_data="transport:u2u7_rent",
        ))

    # Покупка U2-U7 (ур. 6)
    if user_level >= UserLevel.LEGEND:
        builder.row(InlineKeyboardButton(
            text="🟡 Купить U2-U7 (90 000₽, 70 км/ч, 80 км)",
            callback_data="transport:u2u7_buy",
        ))

    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_garage",
    ))
    return builder.as_markup()