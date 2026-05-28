from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud import UserCRUD
from database.models import TransportType, UserTransport
from bot.fsm.states import GameStates
from bot.keyboards.tuning import get_tuning_main_keyboard
from generators.tuning_data import MOTORS, CONTROLLERS, BATTERIES, PENDULUMS, BRAKE_SYSTEMS, VISUALS


router = Router()


async def get_transport(session: AsyncSession, uid: int):
    """Получить запись о транспорте игрока."""
    r = await session.execute(
        select(UserTransport).where(UserTransport.user_id == uid)
    )
    return r.scalar_one_or_none()


@router.callback_query(F.data == "garage:tuning")
@router.callback_query(F.data == "tuning:menu")
async def tuning_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Главное меню тюнинга."""
    await callback.answer()

    user = await UserCRUD(session).get(callback.from_user.id)
    if not user:
        return

    if user.current_transport != TransportType.U2U7_OWN:
        await callback.answer(
            "❌ Тюнинг доступен только для своего U2-U7",
            show_alert=True,
        )
        return

    await state.set_state(GameStates.GARAGE_TUNING)

    t = await get_transport(session, user.id)
    if t is None:
        await callback.answer("❌ Транспорт не найден", show_alert=True)
        return

    mn = "Стоковый 500W"
    for m in MOTORS.values():
        if m["power"] == t.motor_power:
            mn = m["name"]
            break

    cn = f"{t.controller_amps}А"
    for c in CONTROLLERS.values():
        if c["amps"] == t.controller_amps:
            cn = c["name"]
            break

    txt = (
        f"🔧 <b>ТЮНИНГ U2-U7</b>\n\n"
        f"⚡ Мотор: {mn}\n"
        f"🧠 Контроллер: {cn}\n"
        f"🔋 АКБ: {t.battery_voltage or '60V40'}\n"
        f"📏 Пробег: {t.total_km:.0f} км\n\n"
        f"Выберите компонент для замены:"
    )

    await callback.message.edit_text(
        txt,
        reply_markup=get_tuning_main_keyboard(),
        parse_mode="HTML",
    )


# ==================== МОТОР ====================

@router.callback_query(F.data == "tuning:motor")
async def tuning_motor_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    t = await get_transport(session, callback.from_user.id)
    if not t:
        return

    builder = InlineKeyboardBuilder()
    for k, m in MOTORS.items():
        req = m.get("requirements", {})
        if req.get("controller_amps", 0) > t.controller_amps:
            continue
        mk = " ✅" if m["power"] == t.motor_power else ""
        builder.row(InlineKeyboardButton(
            text=f"{m['name']} — {m['price']:,}₽{mk}".replace(",", " "),
            callback_data=f"tuning:buy_motor:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))

    await callback.message.edit_text(
        f"⚡ <b>ВЫБОР МОТОРА</b>\n\nТекущая мощность: {t.motor_power}W\n\nДоступные:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_motor:"))
async def buy_motor(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    mk = callback.data.split(":")[2]
    m = MOTORS.get(mk)
    if not m:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < m["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    t = await get_transport(session, user.id)
    if t:
        await uc.add_balance(user.id, -m["price"])
        t.motor_power = m["power"]
        await session.commit()
        await callback.answer(f"✅ Установлен: {m['name']}")
        await tuning_menu(callback, None, session)


# ==================== КОНТРОЛЛЕР ====================

@router.callback_query(F.data == "tuning:controller")
async def ctrl_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    t = await get_transport(session, callback.from_user.id)
    if not t:
        return

    builder = InlineKeyboardBuilder()
    for k, c in CONTROLLERS.items():
        mk = " ✅" if c["amps"] == t.controller_amps else ""
        builder.row(InlineKeyboardButton(
            text=f"{c['name']} — {c['price']:,}₽{mk}".replace(",", " "),
            callback_data=f"tuning:buy_ctrl:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))

    await callback.message.edit_text(
        f"🧠 <b>КОНТРОЛЛЕР</b>\n\nТок: {t.controller_amps}А",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_ctrl:"))
async def buy_ctrl(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    ck = callback.data.split(":")[2]
    c = CONTROLLERS.get(ck)
    if not c:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < c["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    t = await get_transport(session, user.id)
    if t:
        await uc.add_balance(user.id, -c["price"])
        t.controller_amps = c["amps"]
        await session.commit()
        await callback.answer(f"✅ Установлен: {c['name']}")
        await ctrl_list(callback, session)


# ==================== БАТАРЕЯ ====================

@router.callback_query(F.data == "tuning:battery")
async def bat_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    t = await get_transport(session, callback.from_user.id)
    if not t:
        return

    builder = InlineKeyboardBuilder()
    for k, b in BATTERIES.items():
        bl = f"{b['voltage']}{b['capacity_ah']}"
        mk = " ✅" if bl == (t.battery_voltage or "60V40") else ""
        builder.row(InlineKeyboardButton(
            text=f"{b['name']} — {b['price']:,}₽{mk}".replace(",", " "),
            callback_data=f"tuning:buy_bat:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))

    await callback.message.edit_text(
        f"🔋 <b>АКБ</b>\n\nТекущая: {t.battery_voltage or '60V40'}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_bat:"))
async def buy_bat(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    bk = callback.data.split(":")[2]
    b = BATTERIES.get(bk)
    if not b:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < b["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    t = await get_transport(session, user.id)
    if t:
        await uc.add_balance(user.id, -b["price"])
        t.battery_voltage = f"{b['voltage']}{b['capacity_ah']}"
        await session.commit()
        await callback.answer(f"✅ Установлена: {b['name']}")
        await bat_list(callback, session)


# ==================== МАЯТНИК ====================

@router.callback_query(F.data == "tuning:pendulum")
async def pend_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for k, p in PENDULUMS.items():
        builder.row(InlineKeyboardButton(
            text=f"{p['name']} — {p['price']:,}₽".replace(",", " "),
            callback_data=f"tuning:buy_pend:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))
    await callback.message.edit_text(
        "🛞 <b>МАЯТНИК</b>\n\nВыберите:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_pend:"))
async def buy_pend(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    pk = callback.data.split(":")[2]
    p = PENDULUMS.get(pk)
    if not p:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < p["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    await uc.add_balance(user.id, -p["price"])
    await session.commit()
    await callback.answer(f"✅ Установлен: {p['name']}")


# ==================== ТОРМОЗА ====================

@router.callback_query(F.data == "tuning:brakes")
async def brake_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for k, br in BRAKE_SYSTEMS.items():
        builder.row(InlineKeyboardButton(
            text=f"{br['name']} — {br['price']:,}₽".replace(",", " "),
            callback_data=f"tuning:buy_brake:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))
    await callback.message.edit_text(
        "🛑 <b>ТОРМОЗА</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_brake:"))
async def buy_brake(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    bk = callback.data.split(":")[2]
    br = BRAKE_SYSTEMS.get(bk)
    if not br:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < br["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    await uc.add_balance(user.id, -br["price"])
    await session.commit()
    await callback.answer(f"✅ Установлены: {br['name']}")


# ==================== ВНЕШНИЙ ВИД ====================

@router.callback_query(F.data == "tuning:visual")
async def vis_list(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    builder = InlineKeyboardBuilder()
    for k, v in VISUALS.items():
        builder.row(InlineKeyboardButton(
            text=f"{v['name']} — {v['price']:,}₽".replace(",", " "),
            callback_data=f"tuning:buy_vis:{k}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="tuning:menu"))
    await callback.message.edit_text(
        "🎨 <b>ВНЕШНИЙ ВИД</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("tuning:buy_vis:"))
async def buy_vis(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    vk = callback.data.split(":")[2]
    vis = VISUALS.get(vk)
    if not vis:
        return

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)
    if not user or user.balance < vis["price"]:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return

    await uc.add_balance(user.id, -vis["price"])
    await session.commit()
    await callback.answer(f"✅ Установлено: {vis['name']}")


# ==================== СТАТУС ====================

@router.callback_query(F.data == "tuning:status")
async def tuning_status(callback: types.CallbackQuery, session: AsyncSession):
    await callback.answer()
    t = await get_transport(session, callback.from_user.id)
    if not t:
        return

    mn = "Стоковый 500W"
    for m in MOTORS.values():
        if m["power"] == t.motor_power:
            mn = m["name"]
            break

    cn = f"{t.controller_amps}А"
    for c in CONTROLLERS.values():
        if c["amps"] == t.controller_amps:
            cn = c["name"]
            break

    txt = (
        f"📊 <b>СТАТУС СБОРКИ</b>\n\n"
        f"⚡ Мотор: {mn}\n"
        f"🧠 Контроллер: {cn}\n"
        f"🔋 АКБ: {t.battery_voltage or '60V40'}\n"
        f"📏 Пробег: {t.total_km:.0f} км"
    )

    await callback.message.edit_text(txt, parse_mode="HTML")