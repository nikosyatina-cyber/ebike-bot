import random
from typing import Optional, Dict, Any, List
from database.engine import cache

ROAD_EVENTS = [
    {"id": "pothole", "name": "🕳 Огромная яма", "description": "Прямо по курсу!", "choices": [{"text": "Объехать (+3 мин)", "time_penalty": 3, "safe": True}, {"text": "Рискнуть проскочить", "dice_check": 12, "fail_text": "Прокол!", "fail": "puncture"}]},
    {"id": "dog", "name": "🐕 Собака", "description": "Пёс без поводка!", "choices": [{"text": "Тормозить (+2 мин)", "time_penalty": 2, "safe": True}, {"text": "Объехать", "dice_check": 10, "fail_text": "Столкновение!", "fail": "fall"}]},
    {"id": "gazelle", "name": "🚛 Газель", "description": "Перекрыла двор.", "choices": [{"text": "Ждать (+5 мин)", "time_penalty": 5, "safe": True}, {"text": "По газону", "fine_risk": 800, "fine_text": "Штраф 800₽"}]},
    {"id": "filming", "name": "🎥 Съёмки", "description": "Перекрыт квартал.", "choices": [{"text": "Объехать (+8 мин)", "time_penalty": 8, "safe": True}, {"text": "Попросить", "charisma_check": 14, "success_text": "Пропустили!", "fail_time": 12}]},
    {"id": "grandpa", "name": "🧓 Дедушка", "description": "Медленно идёт.", "choices": [{"text": "Ждать (+1 мин)", "time_penalty": 1, "rep_bonus": 1}, {"text": "Сигналить", "rep_penalty": -1, "time_penalty": 0}]},
    {"id": "scooter_kid", "name": "🚲 Школьник", "description": "На самокате!", "choices": [{"text": "Увернуться", "reaction_check": 13, "fail_text": "Столкновение!", "fail": "fall"}, {"text": "Тормозить (+2 мин)", "time_penalty": 2, "safe": True}]},
    {"id": "broken_light", "name": "🚦 Светофор", "description": "Сломался.", "choices": [{"text": "Ждать (+4 мин)", "time_penalty": 4, "safe": True}, {"text": "Ехать осторожно", "dice_check": 10, "fail_text": "Чуть ДТП! +5 мин.", "fail_time": 5}]},
    {"id": "ice_cream", "name": "🍦 Мороженое", "description": "Очередь.", "choices": [{"text": "Купить (+3 мин)", "time_penalty": 3, "mood_bonus": 10}, {"text": "Мимо", "time_penalty": 0}]},
    {"id": "tourists", "name": "📸 Туристы", "description": "Заблудились.", "choices": [{"text": "Помочь (+2 мин, +XP)", "time_penalty": 2, "xp_bonus": 15}, {"text": "Мимо", "time_penalty": 0}]},
]


class RoadEventGenerator:
    async def get_recent(self, uid: int) -> List[str]:
        d = await cache.get(f"user:{uid}:road_events")
        return d if isinstance(d, list) else []

    async def add(self, uid: int, eid: str):
        r = await self.get_recent(uid)
        r.append(eid)
        await cache.set(f"user:{uid}:road_events", r[-30:], 7*24*3600)

    async def generate(self, uid: int, fall_chance: float = 0.0) -> Optional[Dict]:
        if random.random() > 0.25:
            return None
        recent = await self.get_recent(uid)
        avail = [e for e in ROAD_EVENTS if e["id"] not in recent]
        if not avail:
            await cache.delete(f"user:{uid}:road_events")
            avail = ROAD_EVENTS
        ev = random.choice(avail).copy()
        await self.add(uid, ev["id"])
        if fall_chance > 0:
            for c in ev.get("choices", []):
                if "dice_check" in c:
                    c["dice_check"] = min(19, c["dice_check"] + int(fall_chance * 10))
        return ev


road_event_generator = RoadEventGenerator()