from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from arh.database import get_user, create_user, add_xp
from arh.utils.anti_spam import can_get_xp
from arh.config import XP_PER_MESSAGE

router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    await create_user(user_id, message.from_user.username, message.from_user.first_name)

    await message.answer(
        "⚡ <b>ElectroHub Bot</b>\n\n"
        "Доступные команды:\n"
        "/profile - Ваш профиль\n"
        "/top - Топ пользователей\n"
        "/thanks - Поблагодарить (ответом)\n"
        "/karma - Проверить карму\n"
        "/market [запрос] - Поиск товаров\n"
        "/watch [товар] [цена] - Создать алерт\n"
        "/my_alerts - Мои алерты\n"
        "/del_alert [ID] - Удалить алерт"
    )


@router.message(Command("profile"))
async def profile_command(message: Message):
    from arh.handlers.profile import profile_command as pc
    await pc(message)


@router.message(Command("top"))
async def top_command(message: Message):
    from arh.handlers.profile import top_command as tc
    await tc(message)


@router.message(Command("thanks"))
async def thanks_command(message: Message):
    from arh.handlers.karma import thanks_command as tc
    await tc(message)


@router.message(Command("karma"))
async def karma_command(message: Message):
    from arh.handlers.karma import karma_command as kc
    await kc(message)


@router.message(Command("market"))
async def market_command(message: Message):
    from arh.handlers.market import market_command as mc
    await mc(message)


@router.message(Command("watch"))
async def watch_command(message: Message):
    from arh.handlers.alerts import watch_command as wc
    await wc(message)


@router.message(Command("my_alerts"))
async def my_alerts_command(message: Message):
    from arh.handlers.alerts import my_alerts_command as mac
    await mac(message)


@router.message(Command("del_alert"))
async def del_alert_command(message: Message):
    from arh.handlers.alerts import del_alert_command as dac
    await dac(message)


@router.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith('/'):
        return

    user_id = message.from_user.id
    await create_user(user_id, message.from_user.username, message.from_user.first_name)

    user = await get_user(user_id)
    if user:
        last_time = user[7] or 0
        can_get, _ = can_get_xp(last_time)
        if can_get:
            await add_xp(user_id, XP_PER_MESSAGE)