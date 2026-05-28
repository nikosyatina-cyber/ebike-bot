from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud import UserCRUD
from database.models import User, TransportType, UserTransport, InventoryItem, UserLevel
from database.engine import cache
from bot.fsm.states import GameStates
from bot.keyboards.garage import (
    get_garage_main_keyboard,
    get_service_keyboard,
    get_shop_keyboard,
    get_transport_select_keyboard,
)

router = Router()

SHOP = {
    "lube": {"name": "🧴 Смазка цепи", "price": 150, "item_name": "Смазка цепи"},
    "repair_kit": {"name": "🩹 Ремкомплект", "price": 200, "item_name": "Ремкомплект"},
    "brake_pads": {"name": "🛑 Тормозные колодки", "price": 350, "item_name": "Тормозные колодки"},
    "spare_battery": {"name": "🔋 Запасной аккумулятор", "price": 800, "item_name": "Запасной аккумулятор"},
    "lunchbox": {"name": "🍔 Ланч-бокс", "price": 250, "item_name": "Ланч-бокс"},
    "energy": {"name": "⚡ Энергетик", "price": 150, "item_name": "Энергетик"},
    "raincoat": {"name": "🧥 Дождевик", "price": 400, "item_name": "Дождевик"},
    "gloves": {"name": "🧤 Термоперчатки", "price": 300, "item_name": "Термоперчатки"},
    "powerbank": {"name": "📱 Повербанк", "price": 500, "item_name": "Повербанк"},
}

TPRICES = {
    "wenbox_buy": 35000,
    "u2u7_buy": 90000,
}

TRANSPORT_INFO = {
    TransportType.MECHANIC: {
        "name": "🟤 Механический велосипед",
        "speed": 15,
        "range": "∞",
        "slots": 4,
        "price": "бесплатно",
        "iot": "—",
    },
    TransportType.YANDEX_SCOOTER: {
        "name": "🟡 Яндекс Самокат",
        "speed": 15,
        "range": 20,
        "slots": 1,
        "price": "1₽/мин",
        "iot": "да",
    },
    TransportType.YANDEX_BIKE: {
        "name": "🟣 Яндекс Байк",
        "speed": 25,
        "range": 40,
        "slots": 1,
        "price": "1₽/нед",
        "iot": "да",
    },
    TransportType.WENBOX_RENT: {
        "name": "🔵 Аренда Wenbox без IOT",
        "speed": 45,
        "range": 40,
        "slots": 5,
        "price": "500₽/день",
        "iot": "нет",
    },
    TransportType.U2U7_RENT: {
        "name": "🔴 Аренда U2-U7 без IOT",
        "speed": 60,
        "range": 70,
        "slots": 7,
        "price": "900₽/день",
        "iot": "нет",
    },
    TransportType.WENBOX_OWN: {
        "name": "🟢 Свой Wenbox",
        "speed": 50,
        "range": "45 (можно докупать АКБ)",
        "slots": 5,
        "price": "35 000₽",
        "iot": "нет",
    },
    TransportType.U2U7_OWN: {
        "name": "🟡 Свой U2-U7",
        "speed": 70,
        "range": "80 (база)",
        "slots": 7,
        "price": "90 000₽",
        "iot": "нет",
    },
}

TRANSPORT_BASE_CHARGE = {
    "mechanic": 100,
    "yandex_scooter": 100,
    "yandex_bike": 100,
    "wenbox_rent_iot": 100,
    "wenbox_rent": 100,
    "u2u7_rent_iot": 100,
    "u2u7_rent": 100,
    "wenbox_buy": 100,
    "u2u7_buy": 100,
}

async def get_transport(session: AsyncSession, uid: int):
    """Получить запись о транспорте игрока."""
    r = await session.execute(
        select(UserTransport).where(UserTransport.user_id == uid)
    )
    return r.scalar_one_or_none()


async def get_transport_display(user: User, session: AsyncSession) -> str:
    """Форматирует подробную информацию о текущем транспорте."""
    t_val = user.current_transport
    info = TRANSPORT_INFO.get(t_val)

    if info is None:
        return f"🚲 Транспорт: {t_val.value if hasattr(t_val, 'value') else str(t_val)}"

    lines = [
        f"🚲 <b>{info['name']}</b>",
        f"├── Скорость: {info['speed']} км/ч",
        f"├── Запас хода: {info['range']} км",
        f"├── Слоты: {info['slots']}",
        f"├── Стоимость: {info['price']}",
        f"└── IOT-Модуль: {info['iot']}",
    ]

    # Для своего транспорта показываем износ
    if t_val in [TransportType.WENBOX_OWN, TransportType.U2U7_OWN, TransportType.YANDEX_BIKE]:
        t = await get_transport(session, user.id)
        if t:
            cs = "✅" if t.chain_wear < 40 else "🟡" if t.chain_wear < 70 else "🔴"
            bs = "✅" if t.brake_wear < 40 else "🟡" if t.brake_wear < 70 else "🔴"
            bat = "✅" if t.battery_wear < 40 else "🟡" if t.battery_wear < 70 else "🔴"
            lines.append("")
            lines.append("🔧 <b>Износ:</b>")
            lines.append(f"├── Цепь: {cs} ({100 - t.chain_wear:.0f}%)")
            lines.append(f"├── Тормоза: {bs} ({100 - t.brake_wear:.0f}%)")
            lines.append(f"└── Батарея: {bat} ({100 - t.battery_wear:.0f}%)")

            if t_val == TransportType.U2U7_OWN:
                lines.append("")
                lines.append("⚡ <b>Тюнинг:</b>")
                lines.append(f"├── Мотор: {t.motor_power}W")
                lines.append(f"├── Контроллер: {t.controller_amps}А")
                lines.append(f"└── АКБ: {t.battery_voltage or '60V40'}")

    # Текущий заряд
    lines.append(f"\n🔋 <b>Текущий заряд:</b> {user.battery_charge}%")

    return "\n".join(lines)


async def get_status(session: AsyncSession, user: User, exact: bool = False) -> str:
    """Краткий статус транспорта."""
    t_val = user.current_transport
    info = TRANSPORT_INFO.get(t_val)

    if info is None:
        return f"🚲 {t_val.value if hasattr(t_val, 'value') else str(t_val)}"

    lines = [f"🚲 {info['name']}"]

    if t_val in [TransportType.WENBOX_OWN, TransportType.U2U7_OWN, TransportType.YANDEX_BIKE]:
        t = await get_transport(session, user.id)
        if t:
            if exact:
                lines.append(f"├── Цепь: {100 - t.chain_wear:.0f}%")
                lines.append(f"├── Тормоза: {100 - t.brake_wear:.0f}%")
                lines.append(f"└── АКБ: {100 - t.battery_wear:.0f}%")
            else:
                cs = "✅" if t.chain_wear < 40 else "🟡" if t.chain_wear < 70 else "🔴"
                bs = "✅" if t.brake_wear < 40 else "🟡" if t.brake_wear < 70 else "🔴"
                bat = "✅" if t.battery_wear < 40 else "🟡" if t.battery_wear < 70 else "🔴"
                lines.append(f"├── Цепь: {cs}")
                lines.append(f"├── Тормоза: {bs}")
                lines.append(f"└── АКБ: {bat}")
    else:
        lines.append("└── Обслуживание не требуется")

    lines.append(f"\n🔋 Заряд: {user.battery_charge}%")
    return "\n".join(lines)


async def get_inventory_text(session: AsyncSession, user_id: int) -> str:
    """Форматирует инвентарь."""
    r = await session.execute(
        select(InventoryItem).where(InventoryItem.user_id == user_id)
    )
    items = r.scalars().all()
    if not items:
        return "🎒 Инвентарь пуст."
    lines = ["🎒 Инвентарь:"]
    for item in items:
        lines.append(f"├── {item.item_name} x{item.quantity}")
    return "\n".join(lines)


# ==================== ГЛАВНОЕ МЕНЮ ГАРАЖА ====================

@router.callback_query(F.data == "back_to_garage")
async def back_garage(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    user = await UserCRUD(session).get(callback.from_user.id)
    if user:
        await state.set_state(GameStates.GARAGE_MAIN)
        transport_info = await get_transport_display(user, session)
        text = f"🔧 <b>ГАРАЖ</b>\n\n{transport_info}\n\nВыберите действие:"
        markup = get_garage_main_keyboard()

        if callback.message.text != text or callback.message.reply_markup != markup:
            await callback.message.edit_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )


@router.message(F.text == "🏠 Гараж")
async def cmd_garage_message(
        message: types.Message,
        state: FSMContext,
        session: AsyncSession,
) -> None:
    """Обработчик кнопки 'Гараж' из главного меню."""
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)

    if user is None:
        await message.answer("❌ Профиль не найден. Используйте /start.")
        return

    await state.set_state(GameStates.GARAGE_MAIN)
    transport_info = await get_transport_display(user, session)

    await message.answer(
        f"🔧 <b>ГАРАЖ</b>\n\n{transport_info}\n\nВыберите действие:",
        reply_markup=get_garage_main_keyboard(),
        parse_mode="HTML",
    )


# ==================== ВХОД В ТЮНИНГ ====================




# ==================== ОБСЛУЖИВАНИЕ ====================

@router.callback_query(F.data == "garage:service")
async def service_menu(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    user = await UserCRUD(session).get(callback.from_user.id)
    if user:
        await state.set_state(GameStates.GARAGE_SERVICE)
        transport_info = await get_transport_display(user, session)
        text = f"🔧 <b>ОБСЛУЖИВАНИЕ</b>\n\n{transport_info}\n\nВыберите услугу:"
        markup = get_service_keyboard()

        if callback.message.text != text or callback.message.reply_markup != markup:
            await callback.message.edit_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )


@router.callback_query(F.data == "service:inspect")
async def svc_inspect(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if user and user.balance >= 100:
        await uc.add_balance(user.id, -100)
        await callback.message.edit_text(
            f"🔍 <b>ОСМОТР</b>\n\n{await get_status(session, user, True)}\nСписано: 100₽",
            reply_markup=get_service_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ Недостаточно средств", show_alert=True)


@router.callback_query(F.data == "service:maintenance")
async def svc_maint(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if user and user.balance >= 600:
        t = await get_transport(session, user.id)
        if t:
            t.chain_wear = max(0, t.chain_wear - 25)
            t.brake_wear = max(0, t.brake_wear - 25)
            t.battery_wear = max(0, t.battery_wear - 25)
            await session.commit()
        await uc.add_balance(user.id, -600)
        await callback.message.edit_text(
            f"🔧 <b>ПРОФИЛАКТИКА</b>\n\n{await get_status(session, user)}\nСписано: 600₽",
            reply_markup=get_service_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ Недостаточно средств или нет своего транспорта", show_alert=True)


@router.callback_query(F.data == "service:overhaul")
async def svc_overhaul(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if user and user.balance >= 1800:
        t = await get_transport(session, user.id)
        if t:
            t.chain_wear = 0
            t.brake_wear = 0
            t.battery_wear = 0
            await session.commit()
        await uc.add_balance(user.id, -1800)
        await callback.message.edit_text(
            f"🛠 <b>КАПРЕМОНТ</b>\n\n{await get_status(session, user)}\nСписано: 1800₽\n🎫 Гарантия 2 дня!",
            reply_markup=get_service_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ Недостаточно средств или нет своего транспорта", show_alert=True)


# ==================== МАГАЗИН ====================

@router.callback_query(F.data == "garage:shop")
async def shop_menu(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    await state.set_state(GameStates.GARAGE_SHOP)
    inv = await get_inventory_text(session, callback.from_user.id)
    text = f"🛒 <b>МАГАЗИН РАСХОДНИКОВ</b>\n\n{inv}\n\nВыберите товар:"
    markup = get_shop_keyboard()

    if callback.message.text != text or callback.message.reply_markup != markup:
        await callback.message.edit_text(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("shop:"))
async def shop_buy(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    ik = callback.data.split(":", 1)[1] if ":" in callback.data else ""

    item = SHOP.get(ik)
    if not item:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)

    if not user:
        return

    if user.balance < item["price"]:
        await callback.answer(
            f"❌ Недостаточно средств (нужно {item['price']}₽)",
            show_alert=True,
        )
        return

    await uc.add_balance(user.id, -item["price"])

    r = await session.execute(
        select(InventoryItem).where(
            InventoryItem.user_id == user.id,
            InventoryItem.item_name == item["item_name"],
        )
    )
    inv = r.scalar_one_or_none()

    if inv:
        inv.quantity += 1
    else:
        session.add(InventoryItem(
            user_id=user.id,
            item_name=item["item_name"],
            quantity=1,
        ))
    await session.commit()

    await callback.answer(f"✅ Куплено: {item['name']} за {item['price']}₽")

    inv_text = await get_inventory_text(session, user.id)
    await callback.message.edit_text(
        f"🛒 <b>МАГАЗИН РАСХОДНИКОВ</b>\n\n{inv_text}\n\nВыберите товар:",
        reply_markup=get_shop_keyboard(),
        parse_mode="HTML",
    )


# ==================== СМЕНА ТРАНСПОРТА ====================

@router.callback_query(F.data == "garage:transport_select")
async def transport_menu(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    user = await UserCRUD(session).get(callback.from_user.id)
    if user:
        info = TRANSPORT_INFO.get(user.current_transport, {})
        current_name = info.get("name", str(user.current_transport))

        text = (
            f"🚲 <b>ВЫБОР ТРАНСПОРТА</b>\n\n"
            f"Текущий: {current_name}\n"
            f"💰 Баланс: {user.balance:.0f}₽\n\n"
            f"Выберите транспорт:"
        )
        markup = get_transport_select_keyboard(user.level)

        # Проверяем, изменилось ли сообщение
        if callback.message.text != text or callback.message.reply_markup != markup:
            await callback.message.edit_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )


@router.callback_query(F.data.startswith("transport:"))
async def transport_select(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    tk = callback.data.split(":")[1]
    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user:
        return

    tmap = {
        "mechanic": TransportType.MECHANIC,
        "yandex_scooter": TransportType.YANDEX_SCOOTER,
        "yandex_bike": TransportType.YANDEX_BIKE,
        "wenbox_rent": TransportType.WENBOX_RENT,
        "wenbox_rent_iot": TransportType.WENBOX_RENT,
        "u2u7_rent": TransportType.U2U7_RENT,
        "u2u7_rent_iot": TransportType.U2U7_RENT,
        "wenbox_buy": TransportType.WENBOX_OWN,
        "u2u7_buy": TransportType.U2U7_OWN,
    }
    nt = tmap.get(tk)
    if nt is None:
        return

    # Проверка прав категории «М»
    if tk in ["u2u7_buy", "u2u7_rent", "u2u7_rent_iot"]:
        transport = await get_transport(session, user.id)
        if transport and transport.motor_power > 3000:
            has_license = await cache.get(f"user:{user.id}:license_m")
            if not has_license:
                await callback.answer(
                    "❌ Для мотора >3000W нужны права категории «М»!\n"
                    "Получите их через команду /права",
                    show_alert=True,
                )
                return

    # Стоимость аренды (списывается при каждой смене на арендованный)
    rent_prices = {
        "yandex_scooter": 0,
        "yandex_bike": 0,
        "wenbox_rent": 500,
        "wenbox_rent_iot": 500,
        "u2u7_rent": 900,
        "u2u7_rent_iot": 900,
    }

    if tk in rent_prices and rent_prices[tk] > 0:
        if user.balance < rent_prices[tk]:
            await callback.answer(
                f"❌ Недостаточно средств для аренды (нужно {rent_prices[tk]}₽)",
                show_alert=True,
            )
            return
        await uc.add_balance(user.id, -rent_prices[tk])

    # Покупка транспорта
    if tk in TPRICES:
        if user.balance < TPRICES[tk]:
            await callback.answer(
                f"❌ Недостаточно средств (нужно {TPRICES[tk]:,}₽)".replace(",", " "),
                show_alert=True,
            )
            return
        await uc.add_balance(user.id, -TPRICES[tk])
        new_transport = UserTransport(user_id=user.id, transport_type=nt)
        session.add(new_transport)
        await session.commit()

    # Меняем транспорт
    await uc.set_transport(user.id, nt)

    # Обновляем заряд батареи
    base_charge = TRANSPORT_BASE_CHARGE.get(tk, 100)
    await uc.update_battery(user.id, base_charge)

    transport_names = {
        "mechanic": "🟤 Механический велосипед",
        "yandex_scooter": "🟡 Яндекс Самокат",
        "yandex_bike": "🟣 Яндекс Байк",
        "wenbox_rent_iot": "🔵 Аренда Wenbox с IOT",
        "wenbox_rent": "🔵 Аренда Wenbox без IOT",
        "wenbox_buy": "🟢 Свой Wenbox",
        "u2u7_rent_iot": "🔴 Аренда U2-U7 с IOT",
        "u2u7_rent": "🔴 Аренда U2-U7 без IOT",
        "u2u7_buy": "🟡 Свой U2-U7",
    }
    transport_name = transport_names.get(tk, str(nt))

    # Сообщение о списании
    if tk in rent_prices and rent_prices[tk] > 0:
        await callback.answer(
            f"✅ {transport_name}\nСписано за аренду: {rent_prices[tk]}₽\n🔋 Заряд: {base_charge}%",
            show_alert=True,
        )
    else:
        await callback.answer(
            f"✅ Выбран: {transport_name}\n🔋 Заряд: {base_charge}%",
            show_alert=True,
        )

    await transport_menu(callback, session)