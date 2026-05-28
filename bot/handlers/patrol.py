import random

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from bot.fsm.states import GameStates
from bot.keyboards.platforms import get_order_actions_keyboard
from database.engine import cache
from generators.patrol_zones import generate_patrol_statuses, get_patrol_chance


router = Router()

VIOLATIONS = [
    {"name": "🚲 Езда без шлема", "fine": 500, "chance": 0.40},
    {"name": "📱 Телефон в руке", "fine": 800, "chance": 0.60},
    {"name": "🚦 Проезд на красный", "fine": 2000, "chance": 0.20},
]


async def check_patrol_encounter(
    user_id: int,
    session,
    state: FSMContext,
    callback: types.CallbackQuery,
    current_order: dict,
) -> bool:
    """Проверяет, встретился ли патруль. Возвращает True, если патруль остановил."""
    # Получаем статусы патрулей
    patrol_statuses = await cache.get("patrol_statuses")
    if patrol_statuses is None:
        global_event = await cache.get("global_event:today")
        patrol_statuses = generate_patrol_statuses(global_event)
        await cache.set("patrol_statuses", patrol_statuses, expire_seconds=3600)

    # Определяем зону из заказа
    zone = current_order.get("zone", "Центр") if isinstance(current_order, dict) else "Центр"
    base_chance = get_patrol_chance(zone, patrol_statuses)

    if random.random() > base_chance:
        return False

    v = random.choice(VIOLATIONS)
    if random.random() > v["chance"]:
        return False

    await state.update_data(patrol_violation=v, patrol_state="active")
    await state.set_state(GameStates.PATROL_ENCOUNTER)

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="😇 Остановиться и заплатить",
        callback_data="patrol:stop",
    ))
    builder.row(InlineKeyboardButton(
        text="🗣️ Попробовать договориться",
        callback_data="patrol:talk",
    ))
    builder.row(InlineKeyboardButton(
        text="💨 Уйти в отрыв!",
        callback_data="patrol:flee",
    ))

    status_emoji = {"тихо": "🟢", "обычно": "🟡", "рейд": "🟠", "облава": "🔴"}
    zone_status = patrol_statuses.get(zone, "обычно")

    await callback.message.answer(
        f"🚔 <b>ВНИМАНИЕ! ПАТРУЛЬ!</b>\n\n"
        f"📍 Район: {zone} ({status_emoji.get(zone_status, '🟡')} {zone_status.upper()})\n"
        f"Нарушение: {v['name']}\n"
        f"Штраф: {v['fine']} ₽\n\n"
        f"<b>Ваши действия:</b>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )
    return True


@router.callback_query(F.data.startswith("patrol:"))
async def patrol_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработчик встречи с патрулём."""
    await callback.answer()

    action = callback.data.split(":")[1]
    data = await state.get_data()
    v = data.get("patrol_violation", {})

    uc = UserCRUD(session)
    user = await uc.get(callback.from_user.id)

    if user is None:
        return

    if action == "stop":
        fine = v.get("fine", 500)
        if user.balance >= fine:
            await uc.add_balance(user.id, -fine)
            rt = f"✅ Штраф оплачен: {fine} ₽"
        else:
            user.reputation = max(0, user.reputation - 10)
            await session.commit()
            rt = f"⚠️ Не хватило денег! Репутация -10."

    elif action == "talk":
        roll = random.randint(1, 20)
        if roll >= 14:
            rt = f"🗣️ Договорились! (Бросок: {roll})\nПатруль отпустил без штрафа."
            # Увеличиваем статистику переговоров
            from bot.handlers.achievements import increment_stat
            await increment_stat(user.id, "patrol_talked")
        elif roll == 20:
            rt = f"🗣️ Крит! (Бросок: 20)\nПатрульный — ваш фанат! +5 репутации."
            user.reputation = min(100, user.reputation + 5)
            await session.commit()
            from bot.handlers.achievements import increment_stat
            await increment_stat(user.id, "patrol_talked")
        else:
            fine = v.get("fine", 500) * 2
            if user.balance >= fine:
                await uc.add_balance(user.id, -fine)
                rt = f"❌ Не вышло (Бросок: {roll}). Штраф x2: {fine} ₽"
            else:
                rt = f"❌ Не вышло. Но денег нет. Репутация -15."
                user.reputation = max(0, user.reputation - 15)
                await session.commit()

    elif action == "flee":
        roll = random.randint(1, 20)
        if roll >= 16:
            rt = f"💨 Ушли! (Бросок: {roll})\nПетляли дворами — оторвались!"
        elif roll >= 10:
            rt = f"💨 Почти ушли... (Бросок: {roll})\nНо камера засняла. Штраф x3."
            fine = v.get("fine", 500) * 3
            if user.balance >= fine:
                await uc.add_balance(user.id, -fine)
                rt += f"\nСписано: {fine} ₽"
        else:
            rt = f"❌ Догнали! (Бросок: {roll})\nШтраф x5 и эвакуация."
            fine = v.get("fine", 500) * 5
            if user.balance >= fine:
                await uc.add_balance(user.id, -fine)
            user.reputation = max(0, user.reputation - 20)
            await session.commit()
            rt += f"\nСписано: {fine} ₽\nРепутация: -20"

    await state.update_data(patrol_state="resolved")
    await state.set_state(GameStates.VIEWING_ORDERS)

    await callback.message.edit_text(
        f"🚔 <b>ИТОГ</b>\n\n{rt}",
        parse_mode="HTML",
    )

    await callback.message.answer(
        "📋 Продолжим работу?",
        reply_markup=get_order_actions_keyboard(),
    )