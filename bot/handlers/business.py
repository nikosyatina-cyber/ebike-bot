"""Обработчики собственного бизнеса."""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from database.engine import cache
from generators.business import BUSINESS_TYPES, BusinessSystem


router = Router()


@router.message(Command("business"))
@router.message(Command("бизнес"))
async def cmd_business(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Показывает бизнес игрока."""
    user_id = message.from_user.id
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        await message.reply("❌ Профиль не найден. Используйте /start")
        return

    if user.level.value < 6:
        await message.reply(
            "🏪 <b>СОБСТВЕННЫЙ БИЗНЕС</b>\n\n"
            "❌ Доступно с 6 уровня (👑 Легенда)!\n\n"
            f"Ваш уровень: {user.level.value}\n"
            f"Нужно опыта до легенды: {7000 - user.xp} XP",
            parse_mode="HTML",
        )
        return

    business = await cache.get(f"user:{user_id}:business")

    if business is None:
        lines = [
            "🏪 <b>ОТКРЫТЬ БИЗНЕС</b>\n",
            "Выберите тип бизнеса:\n",
            "💰 Бизнес приносит пассивный доход каждый день!",
            "📈 Можно улучшать до максимального уровня.\n",
        ]

        builder = InlineKeyboardBuilder()
        for biz_type, config in BUSINESS_TYPES.items():
            lines.append(
                f"{config['emoji']} <b>{config['name']}</b>\n"
                f"├── Доход: от {config['base_income']} ₽/день\n"
                f"├── Макс. уровень: {config['max_level']}\n"
                f"└── {config['description']}\n"
            )
            builder.row(types.InlineKeyboardButton(
                text=f"Открыть: {config['name']}",
                callback_data=f"business:start:{biz_type}",
            ))

        await message.reply(
            "\n".join(lines),
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
        return

    biz_type = business.get("type", "shawarma")
    level = business.get("level", 1)
    collected = business.get("collected_today", False)

    info = BusinessSystem.format_business(biz_type, level)

    builder = InlineKeyboardBuilder()
    if not collected:
        builder.row(types.InlineKeyboardButton(
            text="💰 Забрать дневной доход",
            callback_data=f"business:collect:{biz_type}",
        ))
    else:
        builder.row(types.InlineKeyboardButton(
            text="✅ Доход собран — ждите завтра",
            callback_data="business:collected",
        ))

    if level < BUSINESS_TYPES[biz_type]["max_level"]:
        cost = BusinessSystem.get_upgrade_cost(biz_type, level)
        builder.row(types.InlineKeyboardButton(
            text=f"📈 Улучшить бизнес ({cost:,} ₽)".replace(",", " "),
            callback_data=f"business:upgrade:{biz_type}",
        ))

    builder.row(types.InlineKeyboardButton(
        text="🔄 Сменить бизнес (сброс уровня, 50 000₽)",
        callback_data="business:change",
    ))

    status = "💰 Доступен к сбору!" if not collected else "✅ Уже собран сегодня"
    await message.reply(
        f"{info}\n\n📊 Статус: {status}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "business:collected")
async def business_collected(callback: types.CallbackQuery):
    """Доход уже собран."""
    await callback.answer("✅ Доход уже собран сегодня. Приходите завтра!", show_alert=True)


@router.callback_query(F.data == "business:change")
async def business_change(callback: types.CallbackQuery, session: AsyncSession):
    """Смена бизнеса."""
    user_id = callback.from_user.id
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        return

    if user.balance < 50000:
        await callback.answer("❌ Смена бизнеса стоит 50 000 ₽!", show_alert=True)
        return

    await user_crud.add_balance(user_id, -50000)
    await cache.delete(f"user:{user_id}:business")

    await callback.answer("🔄 Бизнес закрыт. Откройте новый!")
    await cmd_business(callback.message, session)


@router.callback_query(F.data.startswith("business:"))
async def business_handler(
    callback: types.CallbackQuery,
    session: AsyncSession,
) -> None:
    """Обработчик бизнеса."""
    await callback.answer()

    parts = callback.data.split(":")
    action = parts[1]
    biz_type = parts[2] if len(parts) > 2 else None

    user_id = callback.from_user.id
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        return

    if action == "start" and biz_type:
        config = BUSINESS_TYPES.get(biz_type)
        if config is None:
            return

        business = {"type": biz_type, "level": 1, "collected_today": True}
        await cache.set(f"user:{user_id}:business", business)

        await callback.message.edit_text(
            f"🎉 <b>БИЗНЕС ОТКРЫТ!</b>\n\n"
            f"{BusinessSystem.format_business(biz_type, 1)}\n\n"
            f"💰 Первый доход будет доступен завтра!\n"
            f"Используйте /business для управления.",
            parse_mode="HTML",
        )

    elif action == "upgrade" and biz_type:
        business = await cache.get(f"user:{user_id}:business")
        if business is None:
            return

        level = business.get("level", 1)
        cost = BusinessSystem.get_upgrade_cost(biz_type, level)

        if cost == 0:
            await callback.answer("✅ Бизнес уже максимального уровня!", show_alert=True)
            return

        if user.balance < cost:
            await callback.answer(f"❌ Недостаточно средств! Нужно {cost:,} ₽".replace(",", " "), show_alert=True)
            return

        await user_crud.add_balance(user_id, -cost)
        business["level"] = level + 1
        await cache.set(f"user:{user_id}:business", business)

        new_income = BusinessSystem.calculate_income(biz_type, level + 1)

        await callback.message.edit_text(
            f"📈 <b>БИЗНЕС УЛУЧШЕН!</b>\n\n"
            f"{BusinessSystem.format_business(biz_type, level + 1)}\n\n"
            f"💸 Потрачено на улучшение: {cost:,} ₽\n"
            f"📊 Новый доход: {new_income:,} ₽/день".replace(",", " "),
            parse_mode="HTML",
        )

    elif action == "collect" and biz_type:
        business = await cache.get(f"user:{user_id}:business")
        if business is None:
            return

        if business.get("collected_today", False):
            await callback.answer("❌ Доход уже собран сегодня! Приходите завтра.", show_alert=True)
            return

        level = business.get("level", 1)
        income = BusinessSystem.calculate_income(biz_type, level)

        await user_crud.add_balance(user_id, income)
        business["collected_today"] = True
        await cache.set(f"user:{user_id}:business", business)

        await callback.message.edit_text(
            f"💰 <b>ДОХОД СОБРАН!</b>\n\n"
            f"Получено: <b>{income:,} ₽</b>\n"
            f"Следующий сбор: завтра\n\n"
            f"{BusinessSystem.format_business(biz_type, level)}".replace(",", " "),
            parse_mode="HTML",
        )