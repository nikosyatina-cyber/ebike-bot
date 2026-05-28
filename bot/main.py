import asyncio
from datetime import datetime
from sqlalchemy import select

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.settings import settings
from database.engine import check_db_connection, create_tables, close_db, cache, async_session
from database.models import User
from bot.utils.logger import log
from bot.middlewares.database import DatabaseMiddleware
from bot.handlers import (
    start, menu, platform, order, garage, patrol,
    tuning, zones_handler, social, achievements, admin,
    chat_integration, skills, faq, group, quests, business, blackmarket,
)
from bot.config import chat_config


async def scheduled_tasks(bot: Bot) -> None:
    """Периодические задачи — каждый час."""
    now = datetime.now()

    from generators.weather_generator import weather_generator
    from generators.global_events import GlobalEventGenerator

    # Обновляем погоду каждый час
    weather = weather_generator.generate()
    await cache.set("weather:today", weather, expire_seconds=3600)

    # Каждые 3 часа — новое глобальное событие
    event_gen = GlobalEventGenerator()
    if now.hour % 3 == 0:
        event = event_gen.generate()
        if event:
            await cache.set("global_event:today", event, expire_seconds=10800)
        else:
            await cache.delete("global_event:today")

    # Формируем сводку
    msg = weather_generator.format_message(weather)

    event = await cache.get("global_event:today")
    if event:
        msg += f"\n\n🌍 <b>АКТИВНОЕ СОБЫТИЕ:</b>\n{event['name']}\n{event['description']}"

    sent_private = 0
    sent_groups = 0

    # 1. Отправляем всем игрокам в личку
    async with async_session() as session:
        result = await session.execute(
            select(User.id).where(User.is_banned == False)
        )
        user_ids = [row[0] for row in result.fetchall()]

        for uid in user_ids:
            try:
                await bot.send_message(
                    chat_id=uid,
                    text=msg,
                    parse_mode="HTML",
                )
                sent_private += 1
            except Exception:
                pass

    # 2. Отправляем в канал объявлений (если настроен)
    if chat_integration.chat_integration and chat_integration.chat_integration.announcements_chat_id:
        try:
            await bot.send_message(
                chat_id=chat_integration.chat_integration.announcements_chat_id,
                text=msg,
                parse_mode="HTML",
            )
        except Exception as e:
            log.warning(f"Не удалось отправить в канал: {e}")

    # 3. Отправляем в общий чат (если настроен)
    if chat_integration.chat_integration and chat_integration.chat_integration.general_chat_id:
        try:
            await bot.send_message(
                chat_id=chat_integration.chat_integration.general_chat_id,
                text=msg,
                parse_mode="HTML",
            )
            sent_groups += 1
        except Exception as e:
            log.warning(f"Не удалось отправить в общий чат: {e}")

    log.info(f"Часовая сводка: {sent_private} в личку, {sent_groups} в чаты ({now.hour}:00)")

    # ==================== ПОЛНОЧЬ: СБРОС ВСЕХ ДАННЫХ ====================
    if now.hour == 0 and now.minute == 0:
        log.info("Начало сброса ежедневных данных...")

        async with async_session() as session:
            # Получаем всех пользователей
            result = await session.execute(select(User.id))
            user_ids = [row[0] for row in result.fetchall()]

            reset_count = 0
            for uid in user_ids:
                try:
                    # Сброс ежедневных заданий
                    await cache.delete(f"user:{uid}:daily_quests")
                    await cache.delete(f"user:{uid}:quest_stats")

                    # Сброс чёрного рынка
                    await cache.delete(f"user:{uid}:blackmarket")

                    # Сброс сбора бизнеса
                    business = await cache.get(f"user:{uid}:business")
                    if business:
                        business["collected_today"] = False
                        await cache.set(f"user:{uid}:business", business)

                    # Сброс daily-статистики
                    stats = await cache.get(f"user:{uid}:stats")
                    if stats:
                        stats["daily"] = 0
                        await cache.set(f"user:{uid}:stats", stats)

                    reset_count += 1
                except Exception as e:
                    log.error(f"Ошибка сброса для пользователя {uid}: {e}")

        log.info(f"Ежедневные данные сброшены для {reset_count} игроков")

        # Отправляем итоги дня в канал
        if chat_integration.chat_integration:
            try:
                await chat_integration.chat_integration.announce_daily_top()
            except Exception as e:
                log.error(f"Ошибка отправки топа дня: {e}")

        # Сброс глобальных данных
        await cache.delete("patrol_statuses")
        await cache.delete("zones:control")
        await cache.delete("zones:names")
        log.info("Глобальные данные сброшены")


async def set_commands(bot: Bot) -> None:
    """Установка команд бота."""
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="orders", description="Взять заказы"),
        BotCommand(command="garage", description="Гараж и транспорт"),
        BotCommand(command="map", description="Карта зон"),
        BotCommand(command="stats", description="Ваш профиль"),
        BotCommand(command="rating", description="Топ дня"),
        BotCommand(command="skills", description="Навыки"),
        BotCommand(command="upgrade", description="Улучшить навык"),
        BotCommand(command="achievements", description="Достижения"),
        BotCommand(command="quests", description="Ежедневные задания"),
        BotCommand(command="business", description="Ваш бизнес"),
        BotCommand(command="blackmarket", description="Чёрный рынок"),
        BotCommand(command="license", description="Права категории М"),
        BotCommand(command="transfer", description="Передать предмет"),
        BotCommand(command="accept", description="Принять предмет"),
        BotCommand(command="patrol", description="Статус патрулей"),
        BotCommand(command="faq", description="Справка"),
    ]

    await bot.delete_my_commands()
    await bot.set_my_commands(commands)


async def main() -> None:
    """Точка входа."""
    log.info("=" * 50)
    log.info("Запуск Е-Байк: Доставка v1.0")
    log.info("=" * 50)

    if not await check_db_connection():
        log.error("Нет подключения к БД. Завершение.")
        return

    await create_tables()
    await cache.init_tables()
    log.info("База данных готова")

    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await set_commands(bot)
    log.info("Команды бота установлены")

    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())

    chat_integration.init_chat_integration(
        bot=bot,
        general_chat_id=chat_config.general_chat_id,
        announcements_chat_id=chat_config.announcements_id,
    )

    # Регистрируем все роутеры
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(platform.router)
    dp.include_router(order.router)
    dp.include_router(garage.router)
    dp.include_router(patrol.router)
    dp.include_router(tuning.router)
    dp.include_router(zones_handler.router)
    dp.include_router(social.router)
    dp.include_router(achievements.router)
    dp.include_router(quests.router)
    dp.include_router(business.router)
    dp.include_router(blackmarket.router)
    dp.include_router(admin.router)
    dp.include_router(faq.router)
    dp.include_router(group.router)
    log.info("Роутеры зарегистрированы")

    # Планировщик задач
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_tasks, 'cron', minute=0, args=(bot,))
    scheduler.start()
    log.info("Планировщик запущен")

    try:
        log.info("Бот запущен. Polling...")
        await dp.start_polling(bot)
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
    finally:
        scheduler.shutdown()
        await close_db()
        await bot.session.close()
        log.info("Бот остановлен.")


if __name__ == "__main__":
    asyncio.run(main())