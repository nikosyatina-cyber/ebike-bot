"""Обработчики ежедневных заданий."""

from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

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
async def cmd_quests(message: types.Message, session: AsyncSession):
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

    for quest in quests:
        stat = quest["stat"]
        target = quest["target"]
        progress = quest_stats.get(stat, 0)
        quest["progress"] = min(progress, target)
        quest["completed"] = progress >= target
        status = "✅" if quest["completed"] else "🔄"
        if quest["completed"]:
            completed_count += 1
        lines.append(f"{status} {quest['name']}: {quest['description']} ({min(progress, target)}/{target})")

    if completed_count == 3:
        lines.append("\n🎁 Все 3 выполнены! /claim_quests — забрать бонус")

    lines.append("\n⏰ Сброс в 00:00")
    await cache.set(f"user:{user_id}:daily_quests", quests, expire_seconds=86400)
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("claim_quests"))
async def cmd_claim_quests(message: types.Message, session: AsyncSession):
    """Забрать награду за выполненные задания."""
    user_id = message.from_user.id
    quests = await cache.get(f"user:{user_id}:daily_quests")
    if quests is None:
        await message.reply("❌ Нет активных заданий. /quests")
        return

    quest_stats = await cache.get(f"user:{user_id}:quest_stats") or {}
    total_xp, total_money, claimed = 0, 0, 0
    all_three = True

    for quest in quests:
        stat, target = quest["stat"], quest["target"]
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
        await message.reply("❌ Нет выполненных заданий.")
        return

    user_crud = UserCRUD(session)
    await user_crud.add_xp(user_id, total_xp)
    await user_crud.add_balance(user_id, total_money)

    bonus_text = ""
    if all_three and claimed == 3:
        gen = DailyQuestsGenerator()
        bonus = gen.generate_bonus()
        total_xp += bonus["xp_reward"]
        total_money += bonus["money_reward"]
        await user_crud.add_xp(user_id, bonus["xp_reward"])
        await user_crud.add_balance(user_id, bonus["money_reward"])
        bonus_text = f"\n🎁 Бонус за все 3: +{bonus['xp_reward']} XP + {bonus['money_reward']} ₽"

    await cache.set(f"user:{user_id}:daily_quests", quests, expire_seconds=86400)
    await message.reply(
        f"🎉 <b>НАГРАДЫ!</b>\n📦 Заданий: {claimed}/3\n⭐ +{total_xp} XP\n💰 +{total_money} ₽{bonus_text}",
        parse_mode="HTML",
    )
