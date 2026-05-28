from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
import time
from arh.database import get_user, add_karma, update_last_karma_time
from arh.config import KARMA_AMOUNT, KARMA_COOLDOWN

router = Router()  # ЭТО КРИТИЧЕСКИ ВАЖНО!


@router.message(Command("thanks"))
async def thanks_command(message: Message):
    if not message.reply_to_message:
        await message.answer("❌ Ответьте на сообщение")
        return

    target = message.reply_to_message.from_user
    sender = message.from_user

    if target.id == sender.id:
        await message.answer("😄 Нельзя благодарить себя!")
        return

    if target.is_bot:
        await message.answer("🤖 Нельзя благодарить ботов!")
        return

    sender_data = await get_user(sender.id)
    if sender_data:
        last_karma = sender_data[8] or 0
        if time.time() - last_karma < KARMA_COOLDOWN:
            wait = int(KARMA_COOLDOWN - (time.time() - last_karma))
            await message.answer(f"⏰ Подождите {wait} сек")
            return

    await add_karma(target.id, KARMA_AMOUNT)
    await update_last_karma_time(sender.id)
    await message.answer(f"✅ +{KARMA_AMOUNT} кармы для {target.first_name}!")


@router.message(Command("karma"))
async def karma_command(message: Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        user = await get_user(target.id)
        karma = user[4] if user else 0
        await message.answer(f"⭐ Карма {target.first_name}: {karma}")
    else:
        user = await get_user(message.from_user.id)
        karma = user[4] if user else 0
        await message.answer(f"⭐ Ваша карма: {karma}")