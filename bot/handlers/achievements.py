from typing import Dict, Any, List

from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from database.engine import cache


router = Router()

ACHIEVEMENTS = {
    "first_order": {
        "name": "🚀 Первый заказ",
        "description": "Выполнить 1 заказ",
        "xp_reward": 50,
        "stat": "orders",
        "threshold": 1,
    },
    "sprinter": {
        "name": "⚡ Спринтер",
        "description": "Выполнить 10 заказов за день",
        "xp_reward": 100,
        "stat": "daily",
        "threshold": 10,
    },
    "capitalist": {
        "name": "💰 Капиталист",
        "description": "Накопить 50 000₽",
        "xp_reward": 200,
        "stat": "balance",
        "threshold": 50000,
    },
    "devil": {
        "name": "🏍 Дьявол",
        "description": "Собрать топ-сборку U2-U7 (5000W)",
        "xp_reward": 500,
        "stat": "has_max_tuning",
        "threshold": 1,
    },
    "invisible": {
        "name": "👻 Невидимка",
        "description": "Выполнить 5 заказов Чёрного рынка без засады",
        "xp_reward": 300,
        "stat": "black_market_safe",
        "threshold": 5,
    },
    "elite_master": {
        "name": "👔 Мастер элиты",
        "description": "Обслужить 10 элитных клиентов с восторгом",
        "xp_reward": 400,
        "stat": "elite_perfect",
        "threshold": 10,
    },
    "smooth_talker": {
        "name": "👮 Свой человек",
        "description": "Договориться с патрулём 5 раз",
        "xp_reward": 150,
        "stat": "patrol_talked",
        "threshold": 5,
    },
    "legend": {
        "name": "🦅 Легенда",
        "description": "Достичь 6 уровня",
        "xp_reward": 1000,
        "stat": "level",
        "threshold": 6,
    },
    "king_of_day": {
        "name": "🏆 Король дня",
        "description": "Занять 1 место в дневном рейтинге 3 раза",
        "xp_reward": 500,
        "stat": "daily_wins",
        "threshold": 3,
    },
    "fighter": {
        "name": "🥊 Боец",
        "description": "Победить в 50 драках за зоны",
        "xp_reward": 750,
        "stat": "fight_wins",
        "threshold": 50,
    },
    "cooperator": {
        "name": "🤝 Кооператор",
        "description": "Выполнить 20 совместных заказов",
        "xp_reward": 300,
        "stat": "coop_orders",
        "threshold": 20,
    },
    "iron_horse": {
        "name": "🏍 Железный конь",
        "description": "Проехать 1 000 км",
        "xp_reward": 400,
        "stat": "total_km",
        "threshold": 1000,
    },
}


async def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Получает статистику игрока."""
    data = await cache.get(f"user:{user_id}:stats")
    if data is None:
        return {
            "orders": 0,
            "daily": 0,
            "balance": 0,
            "level": 1,
            "has_max_tuning": 0,
            "black_market_safe": 0,
            "elite_perfect": 0,
            "patrol_talked": 0,
            "daily_wins": 0,
            "fight_wins": 0,
            "coop_orders": 0,
            "total_km": 0,
        }
    return data


async def update_stats(user_id: int, **kwargs) -> None:
    """Обновляет статистику игрока."""
    stats = await get_user_stats(user_id)
    stats.update(kwargs)
    await cache.set(f"user:{user_id}:stats", stats)


async def increment_stat(user_id: int, stat: str, amount: int = 1) -> None:
    """Увеличивает конкретную статистику."""
    stats = await get_user_stats(user_id)
    stats[stat] = stats.get(stat, 0) + amount
    await cache.set(f"user:{user_id}:stats", stats)


async def update_quest_stats(user_id: int, stat: str, amount: int = 1) -> None:
    """Обновляет статистику для ежедневных заданий."""
    quest_stats = await cache.get(f"user:{user_id}:quest_stats")
    if quest_stats is None:
        quest_stats = {}
    quest_stats[stat] = quest_stats.get(stat, 0) + amount
    await cache.set(f"user:{user_id}:quest_stats", quest_stats, expire_seconds=86400)


async def check_and_award_achievements(
    user_id: int,
    session: AsyncSession,
) -> List[Dict[str, Any]]:
    """Проверяет все достижения и начисляет награды за новые."""
    stats = await get_user_stats(user_id)
    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)

    if user is None:
        return []

    stats["balance"] = user.balance
    stats["level"] = user.level.value

    unlocked = await cache.get(f"user:{user_id}:achievements")
    if unlocked is None or isinstance(unlocked, str):
        unlocked = []

    new_achievements = []

    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id in unlocked:
            continue

        stat_name = ach_data["stat"]
        threshold = ach_data["threshold"]
        current_value = stats.get(stat_name, 0)

        if current_value >= threshold:
            unlocked.append(ach_id)
            await user_crud.add_xp(user_id, ach_data["xp_reward"])
            new_achievements.append(ach_data)

    await cache.set(f"user:{user_id}:achievements", unlocked)
    return new_achievements


@router.message(Command("achievements"))
@router.message(Command("achievs"))
@router.message(Command("ачивки"))
@router.message(Command("достижения"))
async def cmd_achievements(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Показывает достижения игрока."""
    user_id = message.from_user.id

    new_ach = await check_and_award_achievements(user_id, session)

    unlocked = await cache.get(f"user:{user_id}:achievements")
    if unlocked is None or isinstance(unlocked, str):
        unlocked = []

    stats = await get_user_stats(user_id)

    user_crud = UserCRUD(session)
    user = await user_crud.get(user_id)
    if user:
        stats["balance"] = user.balance
        stats["level"] = user.level.value

    lines = ["🏆 <b>ДОСТИЖЕНИЯ</b>\n"]

    for ach_id, ach_data in ACHIEVEMENTS.items():
        stat_name = ach_data["stat"]
        threshold = ach_data["threshold"]
        current = stats.get(stat_name, 0)

        if ach_id in unlocked:
            lines.append(f"✅ {ach_data['name']} — {ach_data['description']}")
        else:
            lines.append(
                f"🔒 {ach_data['name']} — {ach_data['description']} "
                f"({min(current, threshold)}/{threshold})"
            )

    if new_ach:
        lines.append("\n🎉 <b>Новые достижения!</b>")
        for ach in new_ach:
            lines.append(f"✅ {ach['name']} — +{ach['xp_reward']} XP")

    await message.reply("\n".join(lines), parse_mode="HTML")