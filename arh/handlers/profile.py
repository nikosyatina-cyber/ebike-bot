from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from arh.database import get_user, get_top_users
from arh.utils.ranks import get_rank, get_progress

router = Router()


@router.message(Command("profile"))
async def profile_command(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Напишите любое сообщение")
        return

    xp = user[3]
    karma = user[4]
    level = user[5]
    messages = user[6]
    rank = get_rank(xp)
    percent, progress, needed = get_progress(xp)

    bar = "█" * (percent // 5) + "░" * (20 - (percent // 5))
    name = user[2] or user[1] or f"User_{user[0]}"

    text = f"""
⚡ <b>Профиль {name}</b>

🏆 Ранг: {rank}
📊 Уровень: {level}
🔋 XP: {xp}
⭐ Карма: {karma}
💬 Сообщений: {messages}

📈 Прогресс:
<code>{bar}</code> {percent}%
({progress}/{needed} XP)
"""
    await message.answer(text)


@router.message(Command("top"))
async def top_command(message: Message):
    users = await get_top_users(10)

    if not users:
        await message.answer("📊 Нет данных")
        return

    text = "🏆 <b>Топ пользователей</b>\n\n"
    for i, user in enumerate(users, 1):
        name = user[2] or user[1] or f"User_{user[0]}"
        xp = user[3]
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {name} — {xp} XP\n"

    await message.answer(text)