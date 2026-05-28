import asyncio
import random
from datetime import datetime

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from bot.fsm.states import GameStates
from generators.orders import OrderGenerator, Order
from generators.road_events import road_event_generator
from generators.client_events import client_event_generator
from generators.weather_generator import weather_generator
from generators.delivery_time import (
    calculate_delivery_time,
    format_time_remaining,
    get_transport_time_info,
)
from database.engine import cache
from bot.keyboards.platforms import get_order_actions_keyboard
from bot.handlers.patrol import check_patrol_encounter


router = Router()
order_generator = OrderGenerator()


def get_user_display(user) -> str:
    if hasattr(user, 'username') and user.username:
        return f"@{user.username}"
    elif hasattr(user, 'full_name') and user.full_name:
        return user.full_name
    return "Курьер"


def get_delivery_progress_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📋 Детали заказа", callback_data="ride:details"))
    return builder.as_markup()


# ==================== ПРИНЯТЬ ЗАКАЗ ====================

@router.callback_query(F.data == "order:accept")
async def accept_order(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await callback.answer()
    user_crud = UserCRUD(session)
    user = await user_crud.get(callback.from_user.id)
    if user is None:
        return

    user_display = get_user_display(user)
    transport_type = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)

    if transport_type != "mechanic" and user.battery_charge <= 0:
        await callback.answer("🔋 Батарея разряжена! Смените транспорт в гараже.", show_alert=True)
        return

    data = await state.get_data()
    co = data.get("current_order")
    if co is None:
        await callback.message.answer("❌ Нет активного заказа. Нажмите «🔄 Другие заказы».")
        return

    total_distance = co.get("total_distance", 0)
    if transport_type != "mechanic":
        needed_charge = int(total_distance * 2)
        if user.battery_charge < needed_charge:
            await callback.answer(f"🔋 Не хватит заряда! Нужно {needed_charge}%, есть {user.battery_charge}%.", show_alert=True)
            return

    await state.set_state(GameStates.RIDING_TO_RESTAURANT)
    await state.update_data(ride_progress="to_restaurant", time_spent=0, user_display=user_display)

    weather = await cache.get("weather:today") or {}
    time_info = calculate_delivery_time(
        distance_km=co.get("restaurant_distance", 1),
        transport_type=transport_type,
        weather=weather,
    )
    await state.update_data(
        current_time_info=time_info,
        delivery_total_real_seconds=time_info["real_seconds"],
        delivery_game_seconds=time_info["game_seconds"],
    )

    transport_info = get_transport_time_info(transport_type)

    await callback.message.edit_text(
        f"{user_display} 🚴 <b>ЕДЕТ В РЕСТОРАН</b>\n\n"
        f"📋 {co['food']}\n📍 {co['restaurant']}\n📏 {co['restaurant_distance']} км\n"
        f"{transport_info}\n{format_time_remaining(time_info['real_seconds'], time_info['game_seconds'])}\n\n"
        f"<i>⏳ Доставка в реальном времени. Ожидайте...</i>",
        reply_markup=get_delivery_progress_keyboard(),
        parse_mode="HTML",
    )

    asyncio.create_task(
        delivery_timer(
            callback=callback, state=state, session=session,
            user=user, co=co, stage="to_restaurant",
            total_seconds=time_info["real_seconds"],
        )
    )


async def delivery_timer(callback, state, session, user, co, stage, total_seconds):
    user_display = get_user_display(user)
    remaining = total_seconds
    update_interval = max(5, total_seconds // 4)

    while remaining > 0:
        await asyncio.sleep(min(update_interval, remaining))
        remaining -= update_interval
        if remaining <= 0:
            break
        try:
            if random.random() < 0.08 and remaining > 8:
                event = await road_event_generator.generate(user.id)
                if event:
                    await callback.message.answer(
                        f"{user_display} 🚴 <b>В ПУТИ!</b>\n\n{event['name']}\n{event['description']}\n\n"
                        f"⏱️ Осталось: ~{remaining} сек",
                        parse_mode="HTML",
                    )
        except Exception:
            pass

    if stage == "to_restaurant":
        weather = await cache.get("weather:today") or {}
        transport_type = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)
        client_time = calculate_delivery_time(
            distance_km=co.get("client_distance", 1),
            transport_type=transport_type,
            weather=weather,
        )
        await state.update_data(
            ride_progress="to_client",
            delivery_total_real_seconds=client_time["real_seconds"],
            delivery_game_seconds=client_time["game_seconds"],
        )

        stopped = await check_patrol_encounter(
            user_id=user.id, session=session, state=state,
            callback=callback, current_order=co,
        )
        if stopped:
            return

        transport_info = get_transport_time_info(transport_type)
        await callback.message.answer(
            f"{user_display} 🏪 <b>ЗАБРАЛ ЗАКАЗ</b>\n\n"
            f"📋 {co.get('food', '?')}\n📍 Едет к клиенту: {co.get('client_distance', 0)} км\n"
            f"{transport_info}\n{format_time_remaining(client_time['real_seconds'], client_time['game_seconds'])}\n\n"
            f"<i>⏳ Едем...</i>",
            reply_markup=get_delivery_progress_keyboard(),
            parse_mode="HTML",
        )
        asyncio.create_task(
            delivery_timer(
                callback=callback, state=state, session=session,
                user=user, co=co, stage="to_client",
                total_seconds=client_time["real_seconds"],
            )
        )
    elif stage == "to_client":
        await handle_client_event(callback, state, session, user, co)


@router.callback_query(F.data == "ride:details")
async def ride_details(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    co = data.get("current_order")
    if co:
        await callback.message.answer(f"📋 <b>ДЕТАЛИ ЗАКАЗА</b>\n\n{Order(**co).format_message()}", parse_mode="HTML")


# ==================== ОБНОВИТЬ ЗАКАЗЫ ====================

@router.callback_query(F.data == "order:refresh")
async def refresh_orders(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await callback.answer("🔄 Ищем заказы...")
    user_crud = UserCRUD(session)
    user = await user_crud.get(callback.from_user.id)
    if user is None:
        return

    user_display = get_user_display(user)
    data = await state.get_data()
    ps = data.get("platform", "yandex")

    transport_type = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)
    low_battery_warning = ""

    if transport_type != "mechanic" and user.battery_charge <= 0:
        await callback.message.edit_text(
            "🔋 <b>БАТАРЕЯ РАЗРЯЖЕНА!</b>\n\nСмените транспорт в 🏠 Гараже или пересядьте на 🟤 Механику.",
            reply_markup=get_order_actions_keyboard(),
            parse_mode="HTML",
        )
        return
    elif transport_type != "mechanic" and user.battery_charge < 20:
        low_battery_warning = "\n⚠️ <b>Заряд ниже 20%!</b>"

    weather = await cache.get("weather:today")
    if weather is None:
        weather = weather_generator.generate()
        await cache.set("weather:today", weather, expire_seconds=3600)

    wm = weather_generator.get_platform_multiplier(weather, ps)
    orders = order_generator.generate_orders(platform=ps, count=1, weather_multiplier=wm)

    if not orders:
        await callback.message.answer("❌ Заказов пока нет.")
        return

    order = orders[0]
    await state.update_data(current_order=order.to_dict(), user_display=user_display)

    # Считаем время ТОЛЬКО до ресторана (как при принятии)
    time_info = calculate_delivery_time(
        distance_km=order.restaurant_distance,
        transport_type=transport_type,
        weather=weather,
    )
    transport_info = get_transport_time_info(transport_type)

    game_seconds = time_info["game_seconds"]
    if game_seconds < 60:
        time_display = f"{game_seconds} игровых сек"
    else:
        time_display = f"{game_seconds // 60} игровых мин"

    await callback.message.edit_text(
        f"{user_display} 📋 <b>НАЙДЕН ЗАКАЗ</b>\n\n"
        f"{order.format_message()}\n"
        f"{transport_info}\n"
        f"⏱️ До ресторана: {time_display} ({time_info['real_seconds']} сек)\n"
        f"📏 Всего: {order.total_distance} км\n"
        f"💰 Баланс: {user.balance:.0f}₽ | 🔋 Заряд: {user.battery_charge}%{low_battery_warning}\n\n"
        f"<b>Что делаем?</b>",
        reply_markup=get_order_actions_keyboard(),
        parse_mode="HTML",
    )


# ==================== ВРУЧЕНИЕ ЗАКАЗА ====================

async def handle_client_event(callback, state, session, user, co):
    if user is None and session:
        user_crud = UserCRUD(session)
        user = await user_crud.get(callback.from_user.id)
    if user is None:
        return

    user_display = get_user_display(user)
    game_seconds = (await state.get_data()).get("delivery_game_seconds", 0)
    game_display = f"{game_seconds} игровых сек" if game_seconds < 60 else f"{game_seconds // 60} игровых мин"
    pay = co.get("base_pay", 200)
    ev = await client_event_generator.generate(user.id)

    if ev is None:
        if session:
            uc = UserCRUD(session)
            await uc.add_balance(user.id, pay)
            await uc.add_xp(user.id, 15)

            total_distance = co.get("total_distance", 0)
            transport_type = user.current_transport.value if hasattr(user.current_transport, 'value') else str(
                user.current_transport)
            if transport_type != "mechanic":
                new_charge = max(0, user.battery_charge - int(total_distance * 2))
                await uc.update_battery(user.id, new_charge)

            from bot.handlers.achievements import increment_stat, update_stats
            await increment_stat(user.id, "orders")
            await increment_stat(user.id, "daily")
            user = await uc.get(user.id)
            if user:
                await update_stats(user.id, balance=user.balance, level=user.level.value)

            # ===== ДОБАВЛЯЕМ ЗАПИСЬ В РЕЙТИНГ =====
            today = datetime.now().strftime('%Y-%m-%d')
            user = await uc.get(callback.from_user.id)
            await cache.zincrby(
                f"ratings:daily:{today}",
                pay,
                f"{callback.from_user.id}:{user.username or user.full_name if user else 'unknown'}",
            )
            # =====================================

        await state.update_data(current_order=None)
        await state.set_state(GameStates.VIEWING_ORDERS)
        user_refreshed = await UserCRUD(session).get(callback.from_user.id) if session else user

        await callback.message.answer(
            f"{user_display} ✅ <b>ДОСТАВИЛ!</b>\n\n"
            f"📋 {co.get('food', 'Заказ')}\n💰 Оплата: <b>{pay} ₽</b>\n⭐ Опыт: +15 XP\n"
            f"⏱ Игровое время: {game_display}\n"
            f"🔋 Заряд: {user_refreshed.battery_charge if user_refreshed else '?'}%\n\n"
            f"<b>Ищем новый заказ?</b>",
            reply_markup=get_order_actions_keyboard(),
            parse_mode="HTML",
        )
        return

    # ... остальной код с клиентским событием ...

    await state.update_data(current_client_event=ev, pending_client_choices=ev.get("choices", []))
    builder = InlineKeyboardBuilder()
    for i, c in enumerate(ev.get("choices", [])):
        builder.row(InlineKeyboardButton(text=c["text"], callback_data=f"client_choice:{i}"))
    await callback.message.answer(
        f"{user_display} 🏠 <b>КЛИЕНТ</b>\n\n{ev['name']}\n{ev['description']}\n\n<b>Ваши действия:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("client_choice:"))
async def client_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await callback.answer()
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    choices = data.get("pending_client_choices", [])
    co = data.get("current_order", {})
    if idx >= len(choices):
        return

    c = choices[idx]
    tb = c.get("tips_bonus", 0)
    xb = c.get("xp_bonus", 0)
    rp = c.get("rep_penalty", 0)
    rt = ""

    if "strength_check" in c:
        roll = random.randint(1, 20)
        rt = f"💪 Успех! {c.get('success_text', '')}" if roll >= c["strength_check"] else f"💪 {c.get('fail_text', 'Не хватило сил.')}"
    elif "charisma_check" in c:
        roll = random.randint(1, 20)
        rt = f"🗣️ Успех! {c.get('success_text', '')}" if roll >= c["charisma_check"] else f"🗣️ {c.get('fail_text', 'Не вышло.')}"
    elif "chance_success" in c:
        rt = "✅ Получилось!" if random.random() < c["chance_success"] else "❌ Не вышло."
    else:
        rt = f"✅ {c['text']}"

    pay = co.get("base_pay", 200) + tb
    uc = UserCRUD(session)
    await uc.add_balance(callback.from_user.id, pay)
    await uc.add_xp(callback.from_user.id, 15 + xb)

    if rp != 0:
        user = await uc.get(callback.from_user.id)
        if user:
            user.reputation = max(0, min(100, user.reputation + rp))
            await session.commit()

    user = await uc.get(callback.from_user.id)
    if user:
        total_distance = co.get("total_distance", 0)
        transport_type = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)
        if transport_type != "mechanic":
            new_charge = max(0, user.battery_charge - int(total_distance * 2))
            await uc.update_battery(user.id, new_charge)

    from bot.handlers.achievements import increment_stat, update_stats
    await increment_stat(callback.from_user.id, "orders")
    await increment_stat(callback.from_user.id, "daily")
    user = await uc.get(callback.from_user.id)
    if user:
        await update_stats(callback.from_user.id, balance=user.balance, level=user.level.value)

    user_display = get_user_display(user) if user else "Курьер"
    await state.update_data(current_order=None)
    await state.set_state(GameStates.VIEWING_ORDERS)

    today = datetime.now().strftime('%Y-%m-%d')
    user = await uc.get(callback.from_user.id)
    await cache.zincrby(f"ratings:daily:{today}", pay, f"{callback.from_user.id}:{user.username or user.full_name if user else 'unknown'}")

    game_seconds = data.get("delivery_game_seconds", 0)
    game_display = f"{game_seconds} игровых сек" if game_seconds < 60 else f"{game_seconds // 60} игровых мин"

    await callback.message.edit_text(
        f"{user_display} ✅ <b>ДОСТАВИЛ!</b>\n\n"
        f"{data.get('current_client_event', {}).get('name', '')}\n{rt}\n\n"
        f"💰 Оплата: <b>{pay} ₽</b> (+{tb} чаевых)\n⭐ Опыт: +{15 + xb} XP\n"
        f"⏱ Игровое время: {game_display}\n🔋 Заряд: {user.battery_charge if user else '?'}%\n\n"
        f"<b>Ищем новый заказ?</b>",
        reply_markup=get_order_actions_keyboard(),
        parse_mode="HTML",
    )