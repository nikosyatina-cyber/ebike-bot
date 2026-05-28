import random
from typing import Optional, Dict, Any, List
from datetime import date

GLOBAL_EVENTS = [
    {
        "id": "football_final",
        "name": "🏟 ЧМ по футболу",
        "description": "Финал в городе! Спрос x3, пробки 9/10.",
        "dice_range": (1, 1),
        "effects": {
            "demand_multiplier": 3.0,
            "traffic_level": 9,
            "elite_active": True,
            "patrol_density": {"Центр": "рейд"}
        },
    },
    {
        "id": "metro_closed",
        "name": "🚇 Закрытие метро",
        "description": "Метро не работает. Все заказы наземные, расстояния +30%.",
        "dice_range": (2, 2),
        "effects": {
            "distance_multiplier": 1.3,
            "demand_multiplier": 1.5,
        },
    },
    {
        "id": "concert_center",
        "name": "🎤 Концерт в центре",
        "description": "Элитные клиенты активны, патрулей больше.",
        "dice_range": (3, 3),
        "effects": {
            "elite_active": True,
            "patrol_density": {"Центр": "рейд", "Северный": "обычно"},
        },
    },
    {
        "id": "courier_strike",
        "name": "🪧 Забастовка курьеров",
        "description": "В Яндексе оплата x2, штраф за отказ -50 рейтинга.",
        "dice_range": (4, 4),
        "effects": {
            "platform_bonus": {"yandex": 2.0},
            "refusal_penalty": -50,
        },
    },
    {
        "id": "bridge_closed",
        "name": "🚧 Перекрытие моста",
        "description": "Северный район отрезан. Заказы туда +50% оплаты.",
        "dice_range": (5, 5),
        "effects": {
            "zone_bonus": {"north": 1.5},
        },
    },
    {
        "id": "major_accident",
        "name": "💥 Крупное ДТП",
        "description": "Пробки 10/10. Достависта — куча заказов.",
        "dice_range": (6, 6),
        "effects": {
            "traffic_level": 10,
            "platform_bonus": {"dostavista": 1.8},
        },
    },
    {
        "id": "black_friday",
        "name": "🛍 Чёрная пятница",
        "description": "WB и Озон — тройные заказы.",
        "dice_range": (7, 7),
        "effects": {
            "platform_bonus": {"wb": 3.0, "ozon": 3.0},
        },
    },
    {
        "id": "epidemic",
        "name": "🏥 Эпидемия",
        "description": "Аптечные заказы x3. Чёрный рынок рискует.",
        "dice_range": (8, 8),
        "effects": {
            "pharmacy_demand": 3.0,
            "black_market_heat": 20,
        },
    },
    {
        "id": "police_raid",
        "name": "👮 Рейд по городу",
        "description": "Все районы на рейде. Штрафы x2.",
        "dice_range": (9, 9),
        "effects": {
            "patrol_density": {"*": "рейд"},
            "fine_multiplier": 2.0,
        },
    },
    {
        "id": "city_day",
        "name": "🎉 День города",
        "description": "Чаевые x2 на всех платформах. Пробки 8/10.",
        "dice_range": (10, 10),
        "effects": {
            "tips_multiplier": 2.0,
            "traffic_level": 8,
        },
    },
]


class GlobalEventGenerator:
    """Генератор глобальных событий."""

    def generate(self) -> Optional[Dict[str, Any]]:
        """Генерирует глобальное событие (шанс 50%)."""
        roll = random.randint(1, 20)

        for event in GLOBAL_EVENTS:
            min_r, max_r = event["dice_range"]
            if min_r <= roll <= max_r:
                return event

        return None