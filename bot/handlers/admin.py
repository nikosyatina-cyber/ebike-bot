"""Админ-команды."""

import random
from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud import UserCRUD
from database.models import User, UserTransport, UserLevel, TransportType
from database.engine import cache
from bot.utils.logger import log

router = Router()

# ID администраторов (можно добавить в .env позже)
ADMIN_IDS = [8019639750]  # Если пусто — админы все


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS


def format_user_info(user: User) -> str:
    """Форматирует информацию об игроке."""
    level_names = {
        1: "🥚 Стажёр", 2: "🐣 Подаван", 3: "🦊 Гонщик",
        4: "🐺 Матёрый", 5: "🦅 Элита", 6: "👑 Легенда",
    }
    transport_names = {
        "mechanic": "🟤 Механика",
        "yandex_scooter": "🟡 Самокат Яндекс",
        "yandex_bike": "🟣 Байк Яндекс",
        "wenbox_rent": "🔵 Wenbox аренда",
        "u2u7_rent": "🔴 U2-U7 аренда",
        "wenbox_own": "🟢 Wenbox свой",
        "u2u7_own": "🟡 U2-U7 свой",
    }
    t_val = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)

    return (
        f"📊 <b>ИНФО ОБ ИГРОКЕ</b>\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: @{user.username or 'нет'}\n"
        f"Имя: {user.full_name}\n"
        f"Уровень: {level_names.get(user.level.value, '?')} ({user.xp} XP)\n"
        f"Баланс: {user.balance:.0f} ₽\n"
        f"Транспорт: {transport_names.get(t_val, t_val)}\n"
        f"Заряд: {user.battery_charge}%\n"
        f"Репутация: {user.reputation}/100\n"
        f"Забанен: {'⛔ Да' if user.is_banned else '✅ Нет'}\n"
        f"Создан: {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else '?'}"
    )


async def find_user(target: str, session: AsyncSession):
    """Находит пользователя по ID или username."""
    user_crud = UserCRUD(session)
    # Пробуем как ID
    try:
        user_id = int(target)
        return await user_crud.get(user_id)
    except ValueError:
        pass
    # Ищем по username
    result = await session.execute(
        select(User).where(User.username == target.lstrip("@"))
    )
    return result.scalar_one_or_none()


# ==================== ИНФОРМАЦИЯ ОБ ИГРОКЕ ====================

@router.message(Command("admin_user"))
async def cmd_admin_user(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Показать информацию об игроке."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("❌ /admin_user @username или ID")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    await message.answer(format_user_info(user), parse_mode="HTML")


# ==================== ВЫДАТЬ ВАЛЮТУ ====================

@router.message(Command("admin_give"))
async def cmd_admin_give(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Выдать валюту игроку."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("❌ /admin_give @username [сумма]")
        return

    try:
        amount = float(args[1])
    except ValueError:
        await message.answer("❌ Неверная сумма.")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    user_crud = UserCRUD(session)
    await user_crud.add_balance(user.id, amount)
    await message.answer(
        f"✅ Выдано <b>{amount:,.0f} ₽</b> игроку @{user.username or user.id}".replace(",", " "),
        parse_mode="HTML",
    )
    log.info(f"Админ {message.from_user.id} выдал {amount}₽ игроку {user.id}")


# ==================== ВЫДАТЬ ОПЫТ ====================

@router.message(Command("admin_give_xp"))
async def cmd_admin_give_xp(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Выдать опыт игроку."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("❌ /admin_give_xp @username [количество]")
        return

    try:
        amount = int(args[1])
    except ValueError:
        await message.answer("❌ Неверное количество.")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    user_crud = UserCRUD(session)
    await user_crud.add_xp(user.id, amount)
    await message.answer(
        f"✅ Выдано <b>{amount} XP</b> игроку @{user.username or user.id}",
        parse_mode="HTML",
    )
    log.info(f"Админ {message.from_user.id} выдал {amount} XP игроку {user.id}")


# ==================== БАН / РАЗБАН ====================

@router.message(Command("admin_ban"))
async def cmd_admin_ban(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Забанить игрока."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("❌ /admin_ban @username")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    user.is_banned = True
    await session.commit()
    await message.answer(f"⛔ Игрок @{user.username or user.id} забанен.")
    log.info(f"Админ {message.from_user.id} забанил игрока {user.id}")


@router.message(Command("admin_unban"))
async def cmd_admin_unban(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Разбанить игрока."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("❌ /admin_unban @username")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    user.is_banned = False
    await session.commit()
    await message.answer(f"✅ Игрок @{user.username or user.id} разбанен.")
    log.info(f"Админ {message.from_user.id} разбанил игрока {user.id}")


# ==================== РАССЫЛКА ====================

@router.message(Command("admin_broadcast"))
async def cmd_admin_broadcast(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Отправить сообщение всем игрокам."""
    if not is_admin(message.from_user.id):
        return

    text = command.args
    if not text:
        await message.answer("❌ /admin_broadcast [текст]")
        return

    result = await session.execute(
        select(User.id).where(User.is_banned == False)
    )
    user_ids = [row[0] for row in result.fetchall()]

    count = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(
                chat_id=uid,
                text=f"📢 <b>ОБЪЯВЛЕНИЕ</b>\n\n{text}",
                parse_mode="HTML",
            )
            count += 1
        except Exception:
            pass

    await message.answer(f"✅ Сообщение отправлено {count}/{len(user_ids)} игрокам.")
    log.info(f"Админ {message.from_user.id} сделал рассылку: {text[:50]}...")


# ==================== СБРОС ИГРОКА ====================

@router.message(Command("admin_reset"))
async def cmd_admin_reset(
        message: types.Message,
        command: CommandObject,
        session: AsyncSession,
) -> None:
    """Сбросить прогресс игрока."""
    if not is_admin(message.from_user.id):
        return

    args = command.args.split() if command.args else []
    if not args:
        await message.answer("❌ /admin_reset @username")
        return

    user = await find_user(args[0], session)
    if user is None:
        await message.answer("❌ Игрок не найден.")
        return

    user.xp = 0
    user.level = UserLevel.STAGER
    user.balance = 500
    user.battery_charge = 100
    user.reputation = 50
    user.current_transport = TransportType.MECHANIC
    await session.commit()

    # Очищаем кэш
    await cache.delete(f"user:{user.id}:stats")
    await cache.delete(f"user:{user.id}:achievements")
    await cache.delete(f"user:{user.id}:skills")
    await cache.delete(f"user:{user.id}:license_m")

    await message.answer(f"🔄 Игрок @{user.username or user.id} сброшен до начального состояния.")
    log.info(f"Админ {message.from_user.id} сбросил игрока {user.id}")


# ==================== ПРИНУДИТЕЛЬНАЯ СВОДКА ====================

@router.message(Command("admin_weather"))
async def cmd_admin_weather(
    message: types.Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Принудительная отправка сводки погоды всем."""
    if not is_admin(message.from_user.id):
        return

    from generators.weather_generator import weather_generator

    weather = weather_generator.generate()
    await cache.set("weather:today", weather, expire_seconds=3600)

    msg = weather_generator.format_message(weather)

    # Добавляем глобальное событие
    event = await cache.get("global_event:today")
    if event:
        msg += f"\n\n🌍 <b>АКТИВНОЕ СОБЫТИЕ:</b>\n{event['name']}\n{event['description']}"

    sent_private = 0
    sent_chats = 0

    # 1. Всем игрокам в личку
    result = await session.execute(
        select(User.id).where(User.is_banned == False)
    )
    user_ids = [row[0] for row in result.fetchall()]

    for uid in user_ids:
        try:
            await message.bot.send_message(
                chat_id=uid,
                text=msg,
                parse_mode="HTML",
            )
            sent_private += 1
        except Exception:
            pass

    # 2. В канал объявлений и общий чат
    from bot.handlers.chat_integration import chat_integration
    if chat_integration:
        if chat_integration.announcements_chat_id:
            try:
                await message.bot.send_message(
                    chat_id=chat_integration.announcements_chat_id,
                    text=msg,
                    parse_mode="HTML",
                )
                sent_chats += 1
            except Exception:
                pass

        if chat_integration.general_chat_id:
            try:
                await message.bot.send_message(
                    chat_id=chat_integration.general_chat_id,
                    text=msg,
                    parse_mode="HTML",
                )
                sent_chats += 1
            except Exception:
                pass

    await message.answer(
        f"✅ Сводка погоды отправлена!\n"
        f"👥 Игроков в личку: <b>{sent_private}</b>\n"
        f"💬 В чаты/каналы: <b>{sent_chats}</b>",
        parse_mode="HTML",
    )
    log.info(f"Админ {message.from_user.id} отправил сводку ({sent_private} личных, {sent_chats} чатов)")


# ==================== ПРИНУДИТЕЛЬНОЕ ГЛОБАЛЬНОЕ СОБЫТИЕ ====================

@router.message(Command("admin_event"))
async def cmd_admin_event(
    message: types.Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Принудительная установка глобального события и рассылка."""
    if not is_admin(message.from_user.id):
        return

    from generators.global_events import GlobalEventGenerator, GLOBAL_EVENTS

    args = command.args.split() if command.args else []

    if not args:
        events_list = "\n".join([f"• <b>{e['name']}</b> — <code>{e['id']}</code>" for e in GLOBAL_EVENTS])
        await message.answer(
            f"📋 <b>ДОСТУПНЫЕ СОБЫТИЯ:</b>\n\n{events_list}\n\n"
            f"Использование: /admin_event [id]",
            parse_mode="HTML",
        )
        return

    event_id = args[0]
    event = None
    for e in GLOBAL_EVENTS:
        if e["id"] == event_id:
            event = e
            break

    if event is None:
        await message.answer("❌ Событие не найдено. /admin_event для списка.")
        return

    await cache.set("global_event:today", event, expire_seconds=3600)

    msg = f"🌍 <b>ГЛОБАЛЬНОЕ СОБЫТИЕ!</b>\n\n<b>{event['name']}</b>\n{event['description']}"

    sent_private = 0
    sent_chats = 0

    # Всем игрокам
    result = await session.execute(
        select(User.id).where(User.is_banned == False)
    )
    user_ids = [row[0] for row in result.fetchall()]

    for uid in user_ids:
        try:
            await message.bot.send_message(
                chat_id=uid,
                text=msg,
                parse_mode="HTML",
            )
            sent_private += 1
        except Exception:
            pass

    # В чаты
    from bot.handlers.chat_integration import chat_integration
    if chat_integration:
        if chat_integration.announcements_chat_id:
            try:
                await message.bot.send_message(
                    chat_id=chat_integration.announcements_chat_id,
                    text=msg,
                    parse_mode="HTML",
                )
                sent_chats += 1
            except Exception:
                pass

        if chat_integration.general_chat_id:
            try:
                await message.bot.send_message(
                    chat_id=chat_integration.general_chat_id,
                    text=msg,
                    parse_mode="HTML",
                )
                sent_chats += 1
            except Exception:
                pass

    await message.answer(
        f"✅ Установлено событие: <b>{event['name']}</b>\n"
        f"👥 Игроков в личку: <b>{sent_private}</b>\n"
        f"💬 В чаты/каналы: <b>{sent_chats}</b>",
        parse_mode="HTML",
    )
    log.info(f"Админ {message.from_user.id} установил событие {event_id} ({sent_private} личных, {sent_chats} чатов)")

# ==================== ПРИНУДИТЕЛЬНЫЙ ТОП ДНЯ ====================

@router.message(Command("admin_top"))
async def cmd_admin_top(
        message: types.Message,
        session: AsyncSession,
) -> None:
    """Принудительная отправка топа дня."""
    if not is_admin(message.from_user.id):
        return

    from bot.handlers.chat_integration import chat_integration

    if chat_integration:
        await chat_integration.announce_daily_top()
        await message.answer("✅ Топ дня отправлен в канал.")
    else:
        today = datetime.now().strftime('%Y-%m-%d')
        top = await cache.zrevrange(f"ratings:daily:{today}", 0, 9)
        if not top:
            await message.answer("🏆 Топ дня пуст.")
            return
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = ["🏆 <b>ТОП ДНЯ</b>\n"]
        for i, (member, score) in enumerate(top):
            nick = member.split(":", 1)[1] if ":" in member else member
            medal = medals.get(i, f"{i + 1}.")
            lines.append(f"{medal} {nick} — {int(score):,} ₽".replace(",", " "))
        await message.answer("\n".join(lines), parse_mode="HTML")


# ==================== СТАТИСТИКА СЕРВЕРА ====================

@router.message(Command("admin_stats"))
async def cmd_admin_stats(
        message: types.Message,
        session: AsyncSession,
) -> None:
    """Статистика сервера."""
    if not is_admin(message.from_user.id):
        return

    # Количество игроков
    result = await session.execute(select(User.id))
    total_users = len(result.fetchall())

    result = await session.execute(
        select(User.id).where(User.is_banned == False)
    )
    active_users = len(result.fetchall())

    # Сегодняшние заказы
    today = datetime.now().strftime('%Y-%m-%d')
    top = await cache.zrevrange(f"ratings:daily:{today}", 0, -1)
    total_earnings = sum(int(score) for _, score in top) if top else 0

    # Погода
    weather = await cache.get("weather:today") or {}
    temp = weather.get("temperature", "Н/Д")

    # Событие
    event = await cache.get("global_event:today")
    event_name = event.get("name", "Нет") if event else "Нет"

    await message.answer(
        f"📊 <b>СТАТИСТИКА СЕРВЕРА</b>\n\n"
        f"👥 Всего игроков: <b>{total_users}</b>\n"
        f"✅ Активных: <b>{active_users}</b>\n"
        f"📦 Заказов сегодня: <b>{len(top) if top else 0}</b>\n"
        f"💰 Заработано сегодня: <b>{total_earnings:,.0f} ₽</b>\n"
        f"🌡️ Погода: {temp}\n"
        f"🌍 Событие: {event_name}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}".replace(",", " "),
        parse_mode="HTML",
    )


# ==================== ОЧИСТКА КЭША ====================

@router.message(Command("admin_clearcache"))
async def cmd_admin_clearcache(
        message: types.Message,
        session: AsyncSession,
) -> None:
    """Очистить кэш."""
    if not is_admin(message.from_user.id):
        return

    # Сбрасываем только временные данные
    await cache.delete("weather:today")
    await cache.delete("global_event:today")
    await cache.delete("patrol_statuses")
    await cache.delete("zones:control")
    await cache.delete("zones:names")

    await message.answer("✅ Кэш погоды, событий, патрулей и зон очищен.")
    log.info(f"Админ {message.from_user.id} очистил кэш")