import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

# Загружаем токен из .env файла
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    print("Создайте файл .env с содержимым: BOT_TOKEN=ваш_токен")
    exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Создаем бота и диспетчер
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "⚡ <b>ElectroHub Bot</b>\n\n"
        "Доступные команды:\n"
        "/profile - Профиль\n"
        "/top - Топ пользователей\n"
        "/thanks - Поблагодарить\n"
        "/karma - Проверить карму\n"
        "/market [запрос] - Поиск\n"
        "/watch [товар] [цена] - Алерт\n"
        "/my_alerts - Мои алерты"
    )


@dp.message(Command("profile"))
async def profile_command(message: types.Message):
    await message.answer(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"Имя: {message.from_user.first_name}\n"
        f"ID: {message.from_user.id}\n"
        f"XP: 0\n"
        f"Карма: 0\n"
        f"Ранг: 🔋 Новичок"
    )


@dp.message(Command("top"))
async def top_command(message: types.Message):
    await message.answer("🏆 <b>Топ пользователей</b>\n\nПока нет данных.")


@dp.message(Command("karma"))
async def karma_command(message: types.Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.answer(f"⭐ Карма {user.first_name}: 0")
    else:
        await message.answer(f"⭐ Ваша карма: 0")


@dp.message(Command("thanks"))
async def thanks_command(message: types.Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение пользователя")
        return

    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.answer("😄 Нельзя благодарить себя!")
        return

    await message.answer(f"✅ Вы поблагодарили {message.reply_to_message.from_user.first_name}! +5 кармы")


@dp.message(Command("market"))
async def market_command(message: types.Message):
    query = message.text.replace("/market", "").strip()

    if not query:
        await message.answer("🔍 Пример: /market контроллер 48v")
        return

    await message.answer(f"🔍 Ищем <b>{query}</b>...\n\n🛒 Ozon: Товары найдены\n🟣 Wildberries: Товары найдены")


@dp.message(Command("watch"))
async def watch_command(message: types.Message):
    args = message.text.split()

    if len(args) < 3:
        await message.answer("🔔 Пример: /watch контроллер 5000")
        return

    keyword = args[1]
    try:
        price = int(args[2])
    except:
        await message.answer("❌ Цена должна быть числом")
        return

    await message.answer(f"✅ Алерт создан!\n📦 {keyword}\n💰 {price} ₽")


@dp.message(Command("my_alerts"))
async def my_alerts_command(message: types.Message):
    await message.answer("🔔 У вас пока нет алертов")


@dp.message(Command("del_alert"))
async def del_alert_command(message: types.Message):
    await message.answer("❌ У вас нет алертов для удаления")


@dp.message()
async def unknown_command(message: types.Message):
    if message.text and message.text.startswith('/'):
        await message.answer(f"❌ Неизвестная команда\n\nИспользуйте /start")


async def main():
    print("=" * 50)
    print("⚡ ElectroHub Bot запускается...")

    # Получаем информацию о боте
    bot_info = await bot.get_me()
    print(f"✅ Бот: @{bot_info.username}")
    print(f"✅ Имя: {bot_info.first_name}")
    print("=" * 50)
    print("✅ Бот готов к работе!")
    print("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())