"""Статусы районов для патрулей."""

import random
from typing import Dict, Optional

PATROL_ZONES = {
    "Центр": {"status": "обычно", "description": "Всегда под присмотром"},
    "Северный": {"status": "тихо", "description": "Спальный район"},
    "Южный": {"status": "тихо", "description": "Промзона"},
    "Восточный": {"status": "тихо", "description": "Парки и набережные"},
    "Западный": {"status": "обычно", "description": "Новостройки"},
    "Пригород": {"status": "тихо", "description": "Редко патрулируется"},
}

STATUS_EMOJI = {
    "тихо": "🟢",
    "обычно": "🟡",
    "рейд": "🟠",
    "облава": "🔴",
}

STATUS_CHANCES = {
    "тихо": 0.05,
    "обычно": 0.15,
    "рейд": 0.30,
    "облава": 0.50,
}


def generate_patrol_statuses(global_event: Optional[dict] = None) -> Dict[str, str]:
    """Генерирует статусы патрулей по районам."""
    statuses = {}

    for zone, data in PATROL_ZONES.items():
        base_status = data["status"]

        # Если есть глобальное событие с патрулями
        if global_event:
            patrol_density = global_event.get("effects", {}).get("patrol_density", {})
            if "*" in patrol_density:
                base_status = patrol_density["*"]
            elif zone in patrol_density:
                base_status = patrol_density[zone]

        # Случайное изменение (10% шанс)
        if random.random() < 0.10:
            possible = ["тихо", "обычно", "рейд"]
            base_status = random.choice(possible)

        statuses[zone] = base_status

    return statuses


def get_patrol_chance(zone: str, patrol_statuses: Dict[str, str]) -> float:
    """Возвращает шанс встретить патруль в зоне."""
    status = patrol_statuses.get(zone, "обычно")
    return STATUS_CHANCES.get(status, 0.15)


def format_patrol_statuses(statuses: Dict[str, str]) -> str:
    """Форматирует статусы патрулей для сообщения."""
    lines = ["👮 <b>ПАТРУЛИ СЕГОДНЯ:</b>\n"]
    for zone, status in statuses.items():
        emoji = STATUS_EMOJI.get(status, "🟡")
        lines.append(f"{emoji} {zone}: {status.upper()}")
    return "\n".join(lines)