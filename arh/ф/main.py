"""
Telegram парсер - ИСПРАВЛЕННАЯ ВЕРСИЯ БЕЗ ТАЙМАУТОВ
"""

import asyncio
import os
import sys
import warnings
import logging
from datetime import datetime, timedelta
import pandas as pd
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8452708443:AAGb_am2vtCOPmLtkJHoqAKavF3_T_BeRaI"
API_ID = 33653106  # Ваш API ID
API_HASH = "4245da45b17463b4dc84e11f957c5603"
PHONE = "+79898197606"  # Ваш номер телефона

# ========== ПРОКСИ ==========
USE_PROXY = True  # Использовать прокси?

# Настройки прокси (185.59.234.44:8000:2fP50B:BL6qLJ)
PROXY_HOST = "185.59.234.44"  # Адрес прокси
PROXY_PORT = 8000  # Порт прокси
PROXY_USER = "2fP50B"  # Логин (оставьте пустым если нет)
PROXY_PASS = "BL6qLJ"  # Пароль (оставьте пустым если нет)

# Глобальные переменные
client = None
connected = False

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class States(StatesGroup):
    waiting_for_search = State()
    waiting_for_proxy = State()

# Клавиатуры
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Показать все чаты", callback_data="show_all")],
        [InlineKeyboardButton(text="🔍 Найти чат", callback_data="search_chat")],
        [InlineKeyboardButton(text="🔄 Переподключиться", callback_data="reconnect")],
    ])

def period_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕐 24 часа", callback_data="p_1")],
        [InlineKeyboardButton(text="📆 7 дней", callback_data="p_7")],
        [InlineKeyboardButton(text="📅 30 дней", callback_data="p_30")],
        [InlineKeyboardButton(text="🗓 90 дней", callback_data="p_90")],
        [InlineKeyboardButton(text="« Назад", callback_data="back")],
    ])

def chats_menu(chats, page=0):
    buttons = []
    per_page = 8

    for chat in chats[page*per_page:(page+1)*per_page]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📢 {chat['title'][:45]} ({chat.get('users',0)})",
                callback_data=f"id_{chat['id']}"
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"pg_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"📄{page+1}", callback_data="none"))
    if (page+1)*per_page < len(chats):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"pg_{page+1}"))

    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Функции
def get_proxy():
    if not USE_PROXY:
        return None

    import socks

    proxy = {
        'proxy_type': socks.SOCKS5,
        'addr': PROXY_HOST,
        'port': PROXY_PORT,
        'rdns': True
    }

    if PROXY_USER and PROXY_PASS:
        proxy['username'] = PROXY_USER
        proxy['password'] = PROXY_PASS

    return proxy

async def do_auth():
    global client, connected

    print("\n" + "="*60)
    print("АВТОРИЗАЦИЯ TELEGRAM")
    print("="*60)

    proxy = get_proxy()

    if proxy:
        print(f"🔒 Прокси: {PROXY_HOST}:{PROXY_PORT}")
    else:
        print("🌐 Прямое подключение")

    print("⏳ Подключение...")

    try:
        client = TelegramClient(
            'my_session',
            API_ID,
            API_HASH,
            proxy=proxy,
            timeout=60,
            connection_retries=5,
            retry_delay=5
        )

        print("🔄 Устанавливаю соединение...")
        await client.connect()
        print("✅ Соединение установлено!")

        print("🔍 Проверяю авторизацию...")

        if not await client.is_user_authorized():
            print(f"\n📩 Нужна авторизация")
            print(f"📱 Отправляю код на {PHONE}...")

            await client.send_code_request(PHONE)
            print("✅ Код отправлен! Проверьте Telegram\n")

            code = input("📩 Введите код: ").strip()

            if not code:
                print("❌ Код не введен!")
                return False

            print("🔄 Проверяю код...")

            try:
                await client.sign_in(PHONE, code)
                print("✅ Код верный!")
            except SessionPasswordNeededError:
                print("\n🔐 Требуется пароль 2FA")
                pwd = input("🔐 Введите пароль: ").strip()

                if not pwd:
                    print("❌ Пароль не введен!")
                    return False

                print("🔄 Проверяю пароль...")
                await client.sign_in(password=pwd)
                print("✅ Пароль верный!")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                return False

        print("🔄 Получаю данные...")
        me = await client.get_me()

        print(f"\n{'='*60}")
        print(f"✅ АВТОРИЗАЦИЯ УСПЕШНА!")
        print(f"👤 {me.first_name} {me.last_name or ''}")
        print(f"📞 {me.phone}")
        if me.username:
            print(f"🔗 @{me.username}")
        print(f"{'='*60}\n")

        connected = True
        return True

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")

        try:
            await client.disconnect()
            os.remove('my_session.session')
            print("📁 Сессия удалена")
        except:
            pass

        return False

async def get_chats():
    global connected, client

    if not connected or not client:
        return None

    try:
        chats = []
        async for d in client.iter_dialogs():
            if d.is_group or d.is_channel:
                chats.append({
                    'id': d.id,
                    'title': d.name,
                    'users': getattr(d.entity, 'participants_count', 0)
                })
        return sorted(chats, key=lambda x: x['users'], reverse=True)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None

# Команды бота
@dp.message(Command("start"))
async def start(message: Message):
    status = "✅ Подключен" if connected else "❌ Не подключен"

    if USE_PROXY:
        info = f"🔒 Прокси: {PROXY_HOST}:{PROXY_PORT}"
    else:
        info = "🌐 Прямое подключение"

    await message.answer(
        f"👋 Бот-парсер\n\nСтатус: {status}\n{info}",
        reply_markup=main_menu()
    )

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text("🏠 Меню", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "none")
async def none(callback: CallbackQuery):
    await callback.answer()

@dp.callback_query(F.data == "reconnect")
async def reconnect(callback: CallbackQuery):
    global connected
    await callback.answer()
    connected = False

    msg = await callback.message.edit_text("🔄 Переподключение...")

    if await do_auth():
        await msg.edit_text("✅ Подключено!", reply_markup=main_menu())
    else:
        await msg.edit_text("❌ Ошибка!", reply_markup=main_menu())

@dp.callback_query(F.data == "show_all")
async def show_all(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if not connected:
        await callback.message.edit_text("❌ Нет подключения!", reply_markup=main_menu())
        return

    msg = await callback.message.edit_text("⏳ Загрузка...")
    chats = await get_chats()

    if chats is None:
        await msg.edit_text("❌ Ошибка", reply_markup=main_menu())
        return

    if not chats:
        await msg.edit_text("❌ Нет чатов", reply_markup=main_menu())
        return

    await state.update_data(chats=chats)
    await msg.edit_text(f"📋 Чатов: {len(chats)}", reply_markup=chats_menu(chats))

@dp.callback_query(F.data == "search_chat")
async def search_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if not connected:
        await callback.message.edit_text("❌ Нет подключения!", reply_markup=main_menu())
        return

    await callback.message.edit_text("🔍 Введите название чата:")
    await state.set_state(States.waiting_for_search)

@dp.message(States.waiting_for_search)
async def search_do(message: Message, state: FSMContext):
    q = message.text.strip().lower()

    if len(q) < 2:
        await message.answer("❌ Минимум 2 буквы")
        return

    msg = await message.answer(f"🔍 Поиск: {q}...")
    all_chats = await get_chats()

    if not all_chats:
        await msg.edit_text("❌ Нет чатов", reply_markup=main_menu())
        await state.clear()
        return

    found = [c for c in all_chats if q in c['title'].lower()]

    if not found:
        await msg.edit_text("❌ Не найдено", reply_markup=main_menu())
        await state.clear()
        return

    await state.update_data(chats=found)
    await msg.edit_text(f"✅ Найдено: {len(found)}", reply_markup=chats_menu(found))

@dp.callback_query(F.data.startswith("pg_"))
async def page_change(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    data = await state.get_data()
    chats = data.get('chats', [])
    await callback.message.edit_reply_markup(reply_markup=chats_menu(chats, page))
    await callback.answer()

@dp.callback_query(F.data.startswith("id_"))
async def chat_select(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split("_")[1])
    data = await state.get_data()
    chats = data.get('chats', [])

    title = next((c['title'] for c in chats if c['id'] == chat_id), 'Чат')

    await state.update_data(cid=chat_id, cname=title)
    await callback.message.edit_text(f"✅ {title}\nПериод:", reply_markup=period_menu())
    await callback.answer()

@dp.callback_query(F.data.startswith("p_"))
async def parse_start(callback: CallbackQuery, state: FSMContext):
    global client

    days = int(callback.data.split("_")[1])
    data = await state.get_data()

    chat_id = data.get('cid')
    title = data.get('cname', 'Чат')

    if not chat_id:
        await callback.message.edit_text("❌ Ошибка")
        return

    start = datetime.now() - timedelta(days=days)

    await callback.message.edit_text(f"⏳ Парсинг {title}...")
    await callback.answer()

    try:
        entity = await client.get_entity(chat_id)
        users = {}
        total = 0

        async for msg in client.iter_messages(entity, limit=500000):
            if not msg or not msg.date:
                continue

            if msg.date.replace(tzinfo=None) < start:
                break

            if msg.sender_id:
                try:
                    s = await msg.get_sender()
                    name = f"{s.first_name or ''} {s.last_name or ''}".strip() or str(msg.sender_id)
                    username = f"@{s.username}" if s.username else ""
                except:
                    name = str(msg.sender_id)
                    username = ""

                if msg.sender_id not in users:
                    users[msg.sender_id] = {
                        'Пользователь': name,
                        'Username': username,
                        'Сообщений': 0
                    }

                users[msg.sender_id]['Сообщений'] += 1
                total += 1

                if total % 500 == 0:
                    logger.info(f"Собрано {total} сообщений от {len(users)} пользователей")
                    await asyncio.sleep(0.2)

        if not users:
            await callback.message.edit_text("❌ Нет сообщений")
            return

        df = pd.DataFrame(users.values())
        df = df[['Пользователь', 'Username', 'Сообщений']]
        df = df.sort_values('Сообщений', ascending=False)
        df['%'] = (df['Сообщений'] / total * 100).round(1)

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Статистика', index=False)
            ws = writer.sheets['Статистика']
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 10

        await callback.message.answer_document(
            FSInputFile(filename),
            caption=f"📊 {title}\n👥 {len(df)}\n💬 {total}"
        )

        os.remove(filename)

        top = df.head(10)
        text = f"📊 <b>{title}</b>\n🏆 Топ-10:\n\n"

        for i, (_, r) in enumerate(top.iterrows(), 1):
            emoji = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
            user = r['Пользователь'][:20]
            username = f" ({r['Username']})" if r['Username'] else ""
            text += f"{emoji} {user}{username}: {r['Сообщений']} ({r['%']}%)\n"

        await callback.message.answer(text, reply_markup=main_menu())

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {e}")

async def main():
    print("\n" + "="*60)
    print("TELEGRAM CHAT PARSER BOT")
    print("="*60)
    print(f"📱 {PHONE}")

    if USE_PROXY:
        print(f"🔒 {PROXY_HOST}:{PROXY_PORT}")
    else:
        print("🌐 Прямое подключение")

    print("="*60 + "\n")

    for attempt in range(3):
        print(f"\n🔄 Попытка {attempt + 1} из 3...")

        if await do_auth():
            print("🚀 Бот запущен! Откройте Telegram")
            await dp.start_polling(bot)
            return

        if attempt < 2:
            print(f"\n⏳ Жду 5 секунд...")
            await asyncio.sleep(5)

    print("\n❌ Не удалось подключиться!")
    print("Отключите прокси: USE_PROXY = False")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())