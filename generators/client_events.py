import random
from typing import Optional, Dict, Any, List

from database.engine import cache


CLIENT_EVENTS = [
    {
        "id": "grandma_wallet",
        "name": "🧓 Бабушка ищет кошелёк",
        "description": "«Сейчас, милок, где-то тут был...»",
        "choices": [
            {"text": "Терпеливо ждать (+5 мин, +чаевые)", "time_penalty": 5, "tips_bonus": 30},
            {"text": "Уйти, оставить заказ у двери", "rep_penalty": -5, "time_penalty": 0},
        ],
    },
    {
        "id": "businessman_floor",
        "name": "👔 Бизнесмен просит на 15 этаж",
        "description": "«Лифт сломали, но я доплачу за подъём». Проверка Силы.",
        "choices": [
            {"text": "Поднять пешком (проверка Силы)", "strength_check": 14, "success_text": "Заработали +200₽ чаевых!", "fail_text": "Надорвали спину. -10 XP.", "tips_bonus": 200},
            {"text": "Вежливо отказаться", "rep_penalty": -5, "time_penalty": 0},
        ],
    },
    {
        "id": "cat_escape",
        "name": "🐱 Кот сбежал в подъезд",
        "description": "Девушка в панике: «Помогите поймать Барсика!»",
        "choices": [
            {"text": "Помочь поймать (+3 мин, +чаевые)", "time_penalty": 3, "tips_bonus": 50, "xp_bonus": 10},
            {"text": "Извиниться, заказы ждут", "time_penalty": 0},
        ],
    },
    {
        "id": "drunk_client",
        "name": "🤬 Пьяный клиент",
        "description": "Не открывает дверь, кричит что ничего не заказывал.",
        "choices": [
            {"text": "Ждать и звонить ещё раз", "time_penalty": 5, "chance_success": 0.5},
            {"text": "Сдать заказ на склад (-50% оплаты)", "pay_penalty": 0.5},
        ],
    },
    {
        "id": "birthday",
        "name": "🎂 Именинник",
        "description": "«О, курьер! Заходи, у меня торт!»",
        "choices": [
            {"text": "Задержаться на 5 минут (+XP)", "time_penalty": 5, "xp_bonus": 25},
            {"text": "Поздравить и уйти", "time_penalty": 1, "tips_bonus": 20},
        ],
    },
    {
        "id": "mom_stroller",
        "name": "👶 Мама с коляской",
        "description": "Просит помочь занести коляску в подъезд.",
        "choices": [
            {"text": "Помочь (+2 мин, +чаевые)", "time_penalty": 2, "tips_bonus": 40},
            {"text": "Извиниться, спешу", "time_penalty": 0},
        ],
    },
    {
        "id": "blogger",
        "name": "📸 Блогер снимает контент",
        "description": "«Я блогер, можно вас снять для TikTok?»",
        "choices": [
            {"text": "Согласиться (+репутация)", "time_penalty": 2, "rep_bonus": 10, "xp_bonus": 20},
            {"text": "Отказаться, я на работе", "time_penalty": 0},
        ],
    },
    {
        "id": "lost_keys",
        "name": "🔑 Потерял ключи",
        "description": "Клиент не может войти в квартиру. Просит подождать.",
        "choices": [
            {"text": "Подождать (проверка Харизмы)", "charisma_check": 12, "success_text": "Клиент благодарен! Двойные чаевые.", "fail_text": "Зря прождали 10 минут.", "tips_bonus": 100},
            {"text": "Оставить заказ у двери", "time_penalty": 0, "rep_penalty": -3},
        ],
    },
]


class ClientEventGenerator:
    """Генератор клиентских событий."""

    async def get_recent(self, uid: int) -> List[str]:
        """Получает список ID событий за последние 7 дней."""
        d = await cache.get(f"user:{uid}:client_events")
        return d if isinstance(d, list) else []

    async def add(self, uid: int, eid: str) -> None:
        """Добавляет событие в журнал."""
        r = await self.get_recent(uid)
        r.append(eid)
        await cache.set(f"user:{uid}:client_events", r[-20:], expire_seconds=7*24*3600)

    async def generate(self, uid: int) -> Optional[Dict[str, Any]]:
        """Генерирует клиентское событие с шансом 20%."""
        if random.random() > 0.20:
            return None

        recent = await self.get_recent(uid)
        available = [e for e in CLIENT_EVENTS if e["id"] not in recent]

        if not available:
            await cache.delete(f"user:{uid}:client_events")
            available = CLIENT_EVENTS

        event = random.choice(available).copy()
        await self.add(uid, event["id"])
        return event


client_event_generator = ClientEventGenerator()