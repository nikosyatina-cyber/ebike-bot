"""Навыки персонажа."""

from typing import Dict, Any
from database.engine import cache

SKILLS = {
    "strength": {
        "name": "💪 Сила",
        "description": "Влияет на драки, подъём тяжестей, тетрис",
        "max_level": 10,
    },
    "intelligence": {
        "name": "🧠 Интеллект",
        "description": "Влияет на ремонт, тетрис, угрозы",
        "max_level": 10,
    },
    "charisma": {
        "name": "🗣️ Харизма",
        "description": "Влияет на диалоги, торг, чаевые",
        "max_level": 10,
    },
    "reaction": {
        "name": "⚡ Реакция",
        "description": "Влияет на бронь WB, уклонение от ДТП",
        "max_level": 10,
    },
}

SKILL_XP_COST = {
    1: 100,
    2: 250,
    3: 500,
    4: 1000,
    5: 2000,
    6: 4000,
    7: 8000,
    8: 15000,
    9: 30000,
    10: 50000,
}


async def get_skills(user_id: int) -> Dict[str, int]:
    """Получает навыки игрока."""
    data = await cache.get(f"user:{user_id}:skills")
    if data is None:
        return {"strength": 1, "intelligence": 1, "charisma": 1, "reaction": 1}
    return data


async def set_skills(user_id: int, skills: Dict[str, int]) -> None:
    """Сохраняет навыки игрока."""
    await cache.set(f"user:{user_id}:skills", skills)


async def get_skill_level(user_id: int, skill: str) -> int:
    """Получает уровень конкретного навыка."""
    skills = await get_skills(user_id)
    return skills.get(skill, 1)


async def upgrade_skill(user_id: int, skill: str) -> tuple:
    """
    Пытается улучшить навык.
    Возвращает (успех, сообщение).
    """
    skills = await get_skills(user_id)
    current = skills.get(skill, 1)

    if current >= SKILLS[skill]["max_level"]:
        return False, f"❌ {SKILLS[skill]['name']} уже максимального уровня!"

    cost = SKILL_XP_COST.get(current + 1, 50000)

    from database.crud import UserCRUD
    from database.engine import async_session

    async with async_session() as session:
        user_crud = UserCRUD(session)
        user = await user_crud.get(user_id)
        if user is None:
            return False, "❌ Игрок не найден."
        if user.balance < cost:
            return False, f"❌ Недостаточно средств! Нужно {cost:,} ₽".replace(",", " ")
        await user_crud.add_balance(user_id, -cost)

    skills[skill] = current + 1
    await set_skills(user_id, skills)

    return True, f"✅ {SKILLS[skill]['name']} улучшен до уровня {current + 1}! (-{cost:,} ₽)".replace(",", " ")


def get_skill_bonus(skill_level: int) -> int:
    """Возвращает бонус к броску D20 от уровня навыка."""
    return skill_level // 2


def format_skills(skills: Dict[str, int]) -> str:
    """Форматирует навыки для отображения."""
    lines = ["🎯 <b>НАВЫКИ ПЕРСОНАЖА</b>\n"]
    for skill_id, level in skills.items():
        skill_data = SKILLS.get(skill_id)
        if skill_data:
            bar = "█" * level + "░" * (10 - level)
            lines.append(
                f"{skill_data['name']} [{bar}] Ур.{level}\n"
                f"└── {skill_data['description']}\n"
            )
    return "\n".join(lines)