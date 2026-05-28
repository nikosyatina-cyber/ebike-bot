"""Обработчики ежедневных заданий."""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.crud import UserCRUD
from database.engine import cache
from generators.daily_quests import DailyQuestsGenerator


router = Router()


async def update_quest_stats(user_id: int, stat: str, amount: int = 1) -> None:
    """Обновляет статистику для ежедневных заданий."""
    quest_stats = await cache.get(f"user:{user_id}:quest_stats")
    if quest_stats is None:
        quest_stats = {}
    quest_stats[stat] = quest_stats.get(stat, 0) + amount
    await cache.set(f"user:{user_id}:quest_stats", quest_stats, expire_seconds=86400)


@router.message(Command("quests"))
@router.message(Command("задания"))
async def cmd_quests(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Показывает ежедневные задания."""
    user_id = message.from_user.id

    quests = await cache.get(f"user:{user_id}:daily_quests")
    if quests is None:
        generator = DailyQuestsGenerator()
        quests = generator.generate()
        await cache.set(f"user:{user_id}:daily_quests", quests, expire_seconds=86400)

    quest_stats = await cache.get(f"user:{user_id}:quest_stats") or {}

    lines = ["📋 <b>ЕЖЕДНЕВНЫЕ ЗАДАНИЯ</b>\n"]

    completed_count = 0
    for i, quest in enumerate(quests, 1):
        stat = quest["stat"]
        target = quest["target"]
        progress = quest_stats.get(stat, 0)

        quest["progress"] = min(progress, target)
        quest["completed"] = progress >= target

        if quest["completed"]:
            completed_count += 1
            if quest.get("claimed", False):
                status = "✅✅"
            else:
                status = "✅"
        else:
            status = "🔄"

        filled = min(progress, target)
        empty = target - filled
        progress_bar = "█" * filled + "░" * empty

        lines.append(
            f"{status} <b>{quest['name']}</b>\n"
            f"├── {quest['description']}\n"
            f"├── Прогресс: [{progress_bar}] {min(progress, target)}/{target}\n"
            f"└── Награда: {quest['xp_reward']} XP + {quest['money_reward']} ₽\n"
        )

    if completed_count == 3:
        generator = DailyQuestsGenerator()
        bonus = generator.generate_bonus()
        lines.append("\n🎁 <b>БОНУС ЗА ВСЕ 3:</b>")
        lines.append(f"├── +{bonus['xp_reward']} XP")
        lines.append(f"├── +{bonus['money_reward']:,} ₽".replace(",", " "))
        lines.append(f"└── {bonus['description']}")
        lines.append("\n⚠️ Используйте /claim_quests чтобы получить награды!")

    lines.append(f"\n⏰ Сброс заданий: в 00:00")

    await cache.set(f"user:{user_id}:daily_quests", quests, expire_seconds=86400)
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("claim_quests"))
async def cmd_claim_quests(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Забрать награду за выполненные задания."""
    user_id = message.from_user.id

    quests = await cache.get(f"user:{user_id}:daily_quests")
    if quests is None:
        await message.reply("❌ Нет активных заданий. Используйте /quests")
        return

    quest_stats = await cache.get(f"user:{user_id}:quest_stats") or {}

    total_xp = 0
    total_money = 0
    claimed = 0
    all_three = True

    for quest in quests:
        stat = quest["stat"]
        target = quest["target"]
        progress = quest_stats.get(stat, 0)

        if progress >= target:
            if not quest.get("claimed", False):
                total_xp += quest["xp_reward"]
                total_money += quest["money_reward"]
                quest["claimed"] = True
                claimed += 1
        else:
            all_three = False

    if claimed == 0:
        await message.reply(
            "❌ Нет выполненных заданий для получения награды.\n"
            "Используйте /quests чтобы посмотреть прогресс."
        )
        return

    user_crud = UserCRUD(session)
    await user_crud.add_xp(user_id, total_xp)
    await user_crud.add_balance(user_id, total_money)

    bonus_text = ""
    if all_three and claimed == 3:
        generator = DailyQuestsGenerator()
        bonus = generator.generate_bonus()
        total_xp += bonus["xp_reward"]
        total_money += bonus["money_reward"]
        await user_crud.add_xp(user_id, bonus["xp_reward"])
        await user_crud.add_balance(user_id, bonus["money_reward"])
        bonus_text = (
            "\n🎁 Бонус за все 3: +" + str(bonus["xp_reward"]) + " XP + " +
            str(bonus["money_reward"]).replace(",", " ") + " ₽"
        )

    await cache.set(f"user:{user_id}:daily_quests", quests, expire_seconds=86400)

    result_text = (
        "🎉 <b>НАГРАДЫ ПОЛУЧЕНЫ!</b>\n\n"
        "📦 Выполнено заданий: " + str(claimed) + "/3\n"
        "⭐ Опыт: +" + str(total_xp) + " XP\n"
        "💰 Деньги: +" + str(total_money).replace(",", " ") + " ₽"
        + bonus_text
    )

    await message.reply(result_text, parse_mode="HTML")