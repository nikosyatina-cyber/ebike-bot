import random
from typing import Optional, Dict, Any, List
from database.engine import cache

CLIENT_EVENTS = [
    {"id": "grandma_wallet", "name": "🧓 Бабушка", "description": "Ищет кошелёк.", "choices": [{"text": "Ждать (+5 мин)", "time_penalty": 5, "tips_bonus": 30}, {"text": "Уйти", "rep_penalty": -5, "time_penalty": 0}]},
    {"id": "businessman", "name": "👔 Бизнесмен", "description": "15 этаж без лифта.", "choices": [{"text": "Поднять (Сила)", "strength_check": 14, "success_text": "+200₽ чаевых!", "tips_bonus": 200}, {"text": "Отказаться", "rep_penalty": -5}]},
    {"id": "cat", "name": "🐱 Кот", "description": "Сбежал!", "choices": [{"text": "Поймать (+3 мин)", "time_penalty": 3, "tips_bonus": 50, "xp_bonus": 10}, {"text": "Уйти", "time_penalty": 0}]},
    {"id": "drunk", "name": "🤬 Пьяный", "description": "Не открывает.", "choices": [{"text": "Ждать", "time_penalty": 5, "chance_success": 0.5}, {"text": "Сдать (-50%)", "pay_penalty": 0.5}]},
    {"id": "birthday", "name": "🎂 Именинник", "description": "Торт!", "choices": [{"text": "Остаться (+XP)", "time_penalty": 5, "xp_bonus": 25}, {"text": "Поздравить", "time_penalty": 1, "tips_bonus": 20}]},
    {"id": "mom", "name": "👶 Мама", "description": "Занести коляску.", "choices": [{"text": "Помочь (+2 мин)", "time_penalty": 2, "tips_bonus": 40}, {"text": "Отказаться", "time_penalty": 0}]},
    {"id": "blogger", "name": "📸 Блогер", "description": "Снимает TikTok.", "choices": [{"text": "Согласиться", "time_penalty": 2, "rep_bonus": 10, "xp_bonus": 20}, {"text": "Отказаться", "time_penalty": 0}]},
    {"id": "keys", "name": "🔑 Ключи", "description": "Потерял.", "choices": [{"text": "Ждать (Харизма)", "charisma_check": 12, "success_text": "Двойные чаевые!", "tips_bonus": 100}, {"text": "Уйти", "rep_penalty": -3}]},
]


class ClientEventGenerator:
    async def get_recent(self, uid: int) -> List[str]:
        d = await cache.get(f"user:{uid}:client_events")
        return d if isinstance(d, list) else []

    async def add(self, uid: int, eid: str):
        r = await self.get_recent(uid)
        r.append(eid)
        await cache.set(f"user:{uid}:client_events", r[-20:], 7*24*3600)

    async def generate(self, uid: int) -> Optional[Dict]:
        if random.random() > 0.20:
            return None
        recent = await self.get_recent(uid)
        avail = [e for e in CLIENT_EVENTS if e["id"] not in recent]
        if not avail:
            await cache.delete(f"user:{uid}:client_events")
            avail = CLIENT_EVENTS
        ev = random.choice(avail).copy()
        await self.add(uid, ev["id"])
        return ev


client_event_generator = ClientEventGenerator()