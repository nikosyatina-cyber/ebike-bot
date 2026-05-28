ZONES = {
    "center": {"name": "🏙 Центр", "bonus_description": "+15% к чаевым", "tips_multiplier": 1.15},
    "north": {"name": "🏘 Северный", "bonus_description": "+10% к X5 и Магниту", "platform_bonus": {"x5": 1.10, "magnit": 1.10}},
    "south": {"name": "🏭 Южный", "bonus_description": "+10% к Чёрному рынку", "platform_bonus": {"black_market": 1.10}},
    "east": {"name": "🌳 Восточный", "bonus_description": "+10% к ВкусВилл и TopGO", "platform_bonus": {"vkusvill": 1.10, "topgo": 1.10}},
    "west": {"name": "🏗 Западный", "bonus_description": "+15% к Озон и WB", "platform_bonus": {"ozon": 1.15, "wb": 1.15}},
    "suburb": {"name": "🛣 Пригород", "bonus_description": "+25% к оплате", "pay_multiplier": 1.25, "distance_penalty": 1.20},
}


def get_zone_bonus(zone_key: str, platform: str) -> float:
    zone = ZONES.get(zone_key)
    if zone is None:
        return 1.0
    if "pay_multiplier" in zone:
        return zone["pay_multiplier"]
    if "platform_bonus" in zone:
        return zone["platform_bonus"].get(platform, 1.0)
    if "tips_multiplier" in zone:
        return zone["tips_multiplier"]
    return 1.0