"""Обработчики чёрного рынка запчастей."""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud import UserCRUD
from database.models import InventoryItem, UserTransport
from database.engine import cache
from generators.black_market_parts import BlackMarketGenerator


router = Router()


@router.message(Command("blackmarket"))
@router.message(Command("чёрныйрынок"))
async def cmd_blackmarket(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Показывает чёрный рынок."""
    user_id = message.from_user.id
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        await message.reply("❌ Профиль не найден. Используйте /start")
        return

    if user.level.value < 5:
        await message.reply(
            "🏴 <b>ЧЁРНЫЙ РЫНОК</b>\n\n"
            "❌ Доступно с 5 уровня (🦅 Элита)!\n\n"
            f"Ваш уровень: {user.level.value}",
            parse_mode="HTML",
        )
        return

    items = await cache.get(f"user:{user_id}:blackmarket")
    if items is None:
        generator = BlackMarketGenerator()
        items = generator.generate_daily()
        await cache.set(f"user:{user_id}:blackmarket", items, expire_seconds=86400)

    if not items:
        await message.reply("🏴 Сегодня товаров нет. Загляните завтра!")
        return

    lines = [
        f"🏴 <b>ЧЁРНЫЙ РЫНОК ЗАПЧАСТЕЙ</b>\n",
        f"💰 Ваш баланс: {user.balance:,.0f} ₽\n".replace(",", " "),
    ]

    builder = InlineKeyboardBuilder()

    for item in items:
        lines.append(
            f"\n<b>{item['name']}</b>\n"
            f"├── Цена: <b>{item['price']:,} ₽</b> (скидка {item['discount']}%)\n"
            f"├── Состояние: {item['condition']}\n"
            f"└── {item['description']}"
        )
        builder.row(types.InlineKeyboardButton(
            text=f"Купить: {item['name']} — {item['price']:,} ₽".replace(",", " "),
            callback_data=f"bm:buy:{item['id']}",
        ))

    builder.row(types.InlineKeyboardButton(
        text="🔄 Обновить товары (100₽)",
        callback_data="bm:refresh",
    ))

    await message.reply(
        "\n".join(lines),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("bm:"))
async def blackmarket_handler(
    callback: types.CallbackQuery,
    session: AsyncSession,
) -> None:
    """Обработчик чёрного рынка."""
    await callback.answer()

    action = callback.data.split(":")[1]
    user_id = callback.from_user.id
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        return

    if action == "refresh":
        if user.balance < 100:
            await callback.answer("❌ Недостаточно средств (нужно 100₽)", show_alert=True)
            return

        await user_crud.add_balance(user_id, -100)
        generator = BlackMarketGenerator()
        items = generator.generate_daily()
        await cache.set(f"user:{user_id}:blackmarket", items, expire_seconds=86400)

        await callback.answer("🔄 Товары обновлены! (-100₽)")
        await cmd_blackmarket(callback.message, session)
        return

    if action == "buy":
        item_id = callback.data.split(":")[2]

        items = await cache.get(f"user:{user_id}:blackmarket")
        if items is None:
            await callback.answer("❌ Товары не найдены.", show_alert=True)
            return

        item = None
        for it in items:
            if it["id"] == item_id:
                item = it
                break

        if item is None:
            await callback.answer("❌ Товар не найден.", show_alert=True)
            return

        if user.balance < item["price"]:
            await callback.answer(f"❌ Недостаточно средств (нужно {item['price']:,}₽)".replace(",", " "), show_alert=True)
            return

        await user_crud.add_balance(user_id, -item["price"])

        if item["type"] == "consumables":
            for item_name in item.get("items", []):
                result = await session.execute(
                    select(InventoryItem).where(
                        InventoryItem.user_id == user_id,
                        InventoryItem.item_name == item_name,
                    )
                )
                inv = result.scalar_one_or_none()
                if inv:
                    inv.quantity += 1
                else:
                    session.add(InventoryItem(
                        user_id=user_id,
                        item_name=item_name,
                        quantity=1,
                    ))
            await session.commit()
        else:
            result = await session.execute(
                select(UserTransport).where(UserTransport.user_id == user_id)
            )
            transport = result.scalar_one_or_none()

            if transport is None:
                await callback.answer("❌ У вас нет своего транспорта!", show_alert=True)
                return

            if item["type"] == "motor":
                transport.motor_power = item.get("motor_power", transport.motor_power)
            elif item["type"] == "controller":
                transport.controller_amps = item.get("controller_amps", transport.controller_amps)
            elif item["type"] == "battery":
                transport.battery_voltage = item.get("battery_voltage", transport.battery_voltage)

            await session.commit()

        items = [it for it in items if it["id"] != item_id]
        await cache.set(f"user:{user_id}:blackmarket", items, expire_seconds=86400)

        await callback.answer(f"✅ Куплено: {item['name']} за {item['price']:,} ₽".replace(",", " "), show_alert=True)
        await cmd_blackmarket(callback.message, session)