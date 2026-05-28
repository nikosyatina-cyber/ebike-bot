"""Расчёт времени доставки."""

from typing import Dict, Any

# ============================================================
# НАСТРОЙКИ ВРЕМЕНИ
# ============================================================

# Базовое РЕАЛЬНОЕ время на 1 км (в секундах)
TRANSPORT_SPEED = {
    "mechanic": 7,            # 7 сек на 1 км
    "yandex_scooter": 6,      # 6 сек на 1 км
    "yandex_bike": 5,         # 5 сек на 1 км
    "wenbox_rent": 4,         # 4 сек на 1 км
    "u2u7_rent": 3,           # 3 сек на 1 км
    "wenbox_own": 3,          # 3 сек на 1 км
    "u2u7_own": 2,            # 2 сек на 1 км
}

# Множитель: игровое время = реальное × множитель
# 0.33 = игровое в 3 раза быстрее реального
# 0.5 = игровое в 2 раза быстрее реального
GAME_TIME_MULTIPLIER = 0.33

# Минимальное реальное время (секунд)
MIN_DELIVERY_SECONDS = 3

# ============================================================


def calculate_delivery_time(
    distance_km: float,
    transport_type: str,
    weather: Dict[str, Any] = None,
    has_event: bool = False,
) -> Dict[str, Any]:
    """Рассчитывает время доставки."""
    base_speed = TRANSPORT_SPEED.get(transport_type, 5)
    base_seconds = distance_km * base_speed

    weather_penalty = 0
    if weather:
        speed_penalty = weather.get("speed_penalty", 0)
        visibility_penalty = weather.get("visibility_penalty", 0)
        braking_penalty = weather.get("braking_penalty", 0)
        weather_penalty = base_seconds * (speed_penalty + visibility_penalty + braking_penalty)

    event_penalty = 0
    if has_event:
        event_penalty = base_seconds * 0.15

    real_seconds = base_seconds + weather_penalty + event_penalty
    real_seconds = max(MIN_DELIVERY_SECONDS, real_seconds)

    # Игровое время МЕНЬШЕ реального
    game_seconds = real_seconds * GAME_TIME_MULTIPLIER
    game_seconds = max(1, round(game_seconds))

    return {
        "real_seconds": round(real_seconds),
        "game_seconds": game_seconds,
        "base_seconds": round(base_seconds),
        "weather_penalty": round(weather_penalty),
        "event_penalty": round(event_penalty),
    }


def format_time_remaining(real_seconds: int, game_seconds: int) -> str:
    """Форматирует оставшееся время."""
    if real_seconds < 60:
        real_display = f"{real_seconds} сек"
    else:
        mins = real_seconds // 60
        secs = real_seconds % 60
        real_display = f"{mins}:{secs:02d}"

    if game_seconds < 60:
        game_display = f"{game_seconds} сек"
    else:
        mins = game_seconds // 60
        game_display = f"{mins} мин"

    return f"⏱️ Реальное: <b>{real_display}</b> | Игровое: <b>{game_display}</b>"


def get_transport_time_info(transport_type: str) -> str:
    """Возвращает информацию о скорости транспорта."""
    speed = TRANSPORT_SPEED.get(transport_type, 5)

    if speed <= 2:
        emoji = "🚀"
        desc = "Максимальная скорость"
    elif speed <= 3:
        emoji = "🏍"
        desc = "Очень быстро"
    elif speed <= 5:
        emoji = "🚴"
        desc = "Быстро"
    elif speed <= 6:
        emoji = "🚶"
        desc = "Средняя скорость"
    else:
        emoji = "🐌"
        desc = "Не спеша"

    return f"{emoji} {speed} сек/км — {desc}"