"""Генератор ежедневных заданий."""

import random
from typing import Dict, Any, List

DAILY_QUESTS = [
    # Простые задания
    {
        "id": "complete_orders",
        "name": "📦 Доставщик",
        "description": "Выполнить {target} заказов",
        "target_range": (3, 8),
        "xp_reward": 150,
        "money_reward": 300,
        "stat": "orders",
    },
    {
        "id": "earn_tips",
        "name": "💰 Чаевые",
        "description": "Получить чаевые {target} раз",
        "target_range": (2, 5),
        "xp_reward": 100,
        "money_reward": 200,
        "stat": "tips",
    },
    {
        "id": "no_penalties",
        "name": "🛡 Безупречный",
        "description": "Выполнить {target} заказов без штрафов",
        "target_range": (2, 4),
        "xp_reward": 200,
        "money_reward": 400,
        "stat": "perfect_orders",
    },
    # Средние задания
    {
        "id": "yandex_orders",
        "name": "🟡 Яндекс-такси",
        "description": "Выполнить {target} заказов в Яндекс.Еда",
        "target_range": (2, 5),
        "xp_reward": 200,
        "money_reward": 500,
        "stat": "yandex_orders",
    },
    {
        "id": "ride_km",
        "name": "🏍 Дальнобойщик",
        "description": "Проехать {target} км",
        "target_range": (10, 25),
        "xp_reward": 250,
        "money_reward": 400,
        "stat": "total_km",
    },
    {
        "id": "mechanic_orders",
        "name": "🟤 Олдскул",
        "description": "Выполнить {target} заказов на механике",
        "target_range": (1, 3),
        "xp_reward": 300,
        "money_reward": 600,
        "stat": "mechanic_orders",
    },
    # Сложные задания
    {
        "id": "earn_amount",
        "name": "💎 Капитал",
        "description": "Заработать {target} ₽",
        "target_range": (2000, 5000),
        "xp_reward": 400,
        "money_reward": 1000,
        "stat": "earned_today",
    },
    {
        "id": "elite_orders",
        "name": "👔 VIP-обслуживание",
        "description": "Выполнить {target} элитных заказов",
        "target_range": (1, 3),
        "xp_reward": 500,
        "money_reward": 1500,
        "stat": "elite_orders",
    },
    {
        "id": "night_owl",
        "name": "🦉 Ночная сова",
        "description": "Выполнить {target} заказов после 22:00",
        "target_range": (2, 4),
        "xp_reward": 350,
        "money_reward": 800,
        "stat": "night_orders",
    },
    {
        "id": "zone_capture",
        "name": "⚔️ Завоеватель",
        "description": "Захватить {target} зон",
        "target_range": (1, 2),
        "xp_reward": 500,
        "money_reward": 2000,
        "stat": "zone_captures",
    },
]


class DailyQuestsGenerator:
    """Генератор ежедневных заданий."""

    def generate(self) -> List[Dict[str, Any]]:
        """Генерирует 3 случайных задания на день."""
        # Выбираем 1 простое, 1 среднее, 1 сложное
        easy = [q for q in DAILY_QUESTS if q["xp_reward"] <= 200]
        medium = [q for q in DAILY_QUESTS if 200 < q["xp_reward"] <= 350]
        hard = [q for q in DAILY_QUESTS if q["xp_reward"] > 350]

        selected = [
            random.choice(easy),
            random.choice(medium),
            random.choice(hard),
        ]

        # Генерируем конкретные цели
        quests = []
        for quest in selected:
            target = random.randint(*quest["target_range"])
            quest_copy = quest.copy()
            quest_copy["target"] = target
            quest_copy["description"] = quest["description"].format(target=target)
            quest_copy["progress"] = 0
            quest_copy["completed"] = False
            quests.append(quest_copy)

        return quests

    def generate_bonus(self) -> Dict[str, Any]:
        """Генерирует бонус за выполнение всех 3 заданий."""
        return {
            "xp_reward": 500,
            "money_reward": 2000,
            "description": "Бесплатный ремонт транспорта",
        }