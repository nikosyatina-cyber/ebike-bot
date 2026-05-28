"""Система собственного бизнеса."""

from typing import Dict, Any

BUSINESS_TYPES = {
    "shawarma": {
        "name": "Мастерская ",
        "description": "Только замена Камеры/Покрышек/Подшипников.",
        "base_income": 500,
        "upgrade_cost": 5000,
        "max_level": 10,
        "income_per_level": 500,
    },
    "coffee": {
        "name": "☕ Кофе с собой",
        "description": "Кофе, чай, круассаны. Любят офисные работники.",
        "base_income": 800,
        "upgrade_cost": 8000,
        "max_level": 8,
        "income_per_level": 800,
    },
    "sushi": {
        "name": "Магазин ElectroHub",
        "description": "Элитный магазин, Где есть всё ",
        "base_income": 1200,
        "upgrade_cost": 12000,
        "max_level": 6,
        "income_per_level": 1200,
    },
}


class BusinessSystem:
    """Система бизнеса."""

    @staticmethod
    def calculate_income(business_type: str, level: int) -> int:
        """Рассчитывает доход бизнеса."""
        config = BUSINESS_TYPES.get(business_type)
        if config is None:
            return 0
        return config["base_income"] + (level - 1) * config["income_per_level"]

    @staticmethod
    def get_upgrade_cost(business_type: str, current_level: int) -> int:
        """Рассчитывает стоимость улучшения."""
        config = BUSINESS_TYPES.get(business_type)
        if config is None or current_level >= config["max_level"]:
            return 0
        return config["upgrade_cost"] * current_level

    @staticmethod
    def format_business(business_type: str, level: int) -> str:
        """Форматирует информацию о бизнесе."""
        config = BUSINESS_TYPES.get(business_type)
        if config is None:
            return "❌ Бизнес не найден."

        income = BusinessSystem.calculate_income(business_type, level)
        upgrade_cost = BusinessSystem.get_upgrade_cost(business_type, level)

        lines = [
            f"🏪 <b>{config['name']}</b>",
            f"├── Уровень: {level}/{config['max_level']}",
            f"├── Доход: {income} ₽/день",
            f"├── Описание: {config['description']}",
        ]

        if level < config["max_level"]:
            lines.append(f"└── Улучшение: {upgrade_cost} ₽")
        else:
            lines.append(f"└── Максимальный уровень!")

        return "\n".join(lines)