"""Чёрный рынок запчастей."""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime

# Товары чёрного рынка (со скидкой от 30% до 70%)
BLACK_MARKET_ITEMS = [
    # Моторы
    {
        "name": "Мотор 2000W (б/у)",
        "original_price": 15000,
        "discount_range": (0.3, 0.6),
        "condition": "повезёт",
        "type": "motor",
        "motor_power": 2000,
        "description": "Снят с полицейского конфиската. Работает через раз, но дёшево!",
    },
    {
        "name": "Мотор 3000W (краденый)",
        "original_price": 25000,
        "discount_range": (0.4, 0.7),
        "condition": "рискованный",
        "type": "motor",
        "motor_power": 3000,
        "description": "Без документов. Если остановят — скажешь что сам собрал.",
    },
    {
        "name": "Мотор 5000W (списанный)",
        "original_price": 70000,
        "discount_range": (0.3, 0.5),
        "condition": "требует ремонта",
        "type": "motor",
        "motor_power": 5000,
        "description": "С гоночного скутера. Сломался на 3 круге, но ещё поживёт.",
    },
    # Контроллеры
    {
        "name": "Контроллер 120А (серый)",
        "original_price": 14000,
        "discount_range": (0.4, 0.6),
        "condition": "нормальный",
        "type": "controller",
        "controller_amps": 120,
        "description": "Из Китая напрямую. Прошивка на китайском, но едет.",
    },
    {
        "name": "Контроллер 300А (тюненый)",
        "original_price": 55000,
        "discount_range": (0.5, 0.7),
        "condition": "перегретый",
        "type": "controller",
        "controller_amps": 300,
        "description": "Разогнан до предела. Может сгореть при первом запуске.",
    },
    # Батареи
    {
        "name": "АКБ 72V 60Ah (б/у)",
        "original_price": 25000,
        "discount_range": (0.3, 0.5),
        "condition": "держит заряд",
        "type": "battery",
        "battery_voltage": "72V60",
        "description": "С электромобиля. Тяжёлая, но мощная.",
    },
    {
        "name": "АКБ 72V 80Ah (восстановленная)",
        "original_price": 45000,
        "discount_range": (0.4, 0.6),
        "condition": "после ремонта",
        "type": "battery",
        "battery_voltage": "72V80",
        "description": "Была в пожаре, но ячейки заменили. Риск есть.",
    },
    # Расходники
    {
        "name": "Набор расходников (краденый)",
        "original_price": 2000,
        "discount_range": (0.5, 0.7),
        "condition": "в упаковке",
        "type": "consumables",
        "items": ["Смазка цепи", "Ремкомплект", "Тормозные колодки"],
        "description": "Со склада Яндекс.Еды. Спёрли свои же курьеры.",
    },
]


class BlackMarketGenerator:
    """Генератор чёрного рынка."""

    def generate_daily(self) -> List[Dict[str, Any]]:
        """Генерирует 2-4 товара на день."""
        count = random.randint(2, 4)
        items = random.sample(BLACK_MARKET_ITEMS, min(count, len(BLACK_MARKET_ITEMS)))

        result = []
        for item in items:
            discount = random.uniform(*item["discount_range"])
            price = int(item["original_price"] * (1 - discount))
            item_copy = item.copy()
            item_copy["discount"] = round(discount * 100)
            item_copy["price"] = price
            item_copy["id"] = f"bm_{random.randint(1000, 9999)}"
            result.append(item_copy)

        return result