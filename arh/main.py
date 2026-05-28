import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from arh.config import TOKEN
from arh.database import init_db, close_db
from arh.scheduler import start_scheduler

# Импорт всех роутеров
from arh.handlers import router as xp_router
from arh.handlers.karma import router as karma_router
from arh.handlers import router as profile_router
from arh.handlers.market import router as market_router
from arh.handlers.alerts import router as alerts_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


async def on_startup():
    logger.info("Запуск бота...")
    await init_db()
    start_scheduler(bot)
    logger.info("Бот готов!")


async def on_shutdown():
    logger.info("Остановка...")
    await close_db()
    await bot.session.close()


async def main():
    # Регистрация ВСЕХ роутеров
    dp.include_router(xp_router)
    dp.include_router(karma_router)
    dp.include_router(profile_router)
    dp.include_router(market_router)
    dp.include_router(alerts_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    print("=" * 50)
    print("⚡ ElectroHub Bot запущен!")
    print("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())