import json
from datetime import datetime
from typing import Optional

from aiogram import Bot
from loguru import logger

from database.engine import cache
from generators.weather_generator import weather_generator
from generators.global_events import GlobalEventGenerator


class ChatIntegration:
    """Класс для отправки системных сообщений в общий чат."""

    def __init__(
        self,
        bot: Bot,
        general_chat_id: Optional[int] = None,
        announcements_chat_id: Optional[int] = None,
    ):
        self.bot = bot
        self.general_chat_id = general_chat_id
        self.announcements_chat_id = announcements_chat_id

    async def announce_hourly(self, weather: dict) -> None:
        """Ежечасная сводка погоды."""
        if self.announcements_chat_id is None:
            return

        from generators.weather_generator import weather_generator as wg

        msg = wg.format_message(weather)

        # Добавляем глобальное событие если есть
        event = await cache.get("global_event:today")
        if event:
            msg += f"\n\n🌍 <b>АКТИВНОЕ СОБЫТИЕ:</b>\n{event.get('name', '')}\n{event.get('description', '')}"

        await self.send_to_announcements(msg)

    async def send_to_general(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправить сообщение в общий чат."""
        if self.general_chat_id is None:
            return False
        try:
            await self.bot.send_message(
                chat_id=self.general_chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки в общий чат: {e}")
            return False

    async def send_to_announcements(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправить сообщение в канал объявлений."""
        if self.announcements_chat_id is None:
            return False
        try:
            await self.bot.send_message(
                chat_id=self.announcements_chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
            return False

    async def announce_daily_start(self, weather: dict) -> None:
        """Утренняя сводка."""
        msg = weather_generator.format_message(weather)

        # Добавляем глобальное событие
        event_gen = GlobalEventGenerator()
        event = event_gen.generate()
        if event:
            await cache.set("global_event:today", event, expire_seconds=24 * 3600)
            msg += f"\n\n🌍 <b>ГЛОБАЛЬНОЕ СОБЫТИЕ:</b>\n{event['name']}\n{event['description']}"
        else:
            await cache.delete("global_event:today")

        await self.send_to_announcements(msg)

    async def announce_daily_top(self) -> None:
        """Топ дня."""
        today = datetime.now().strftime('%Y-%m-%d')
        top = await cache.zrevrange(f"ratings:daily:{today}", 0, 9)

        if not top:
            return

        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = ["🤖 <b>Е-Байк Бот</b>\n\n🏆 <b>ТОП ДНЯ</b>\n"]

        for i, (member, score) in enumerate(top):
            nick = member.split(":", 1)[1] if ":" in member else member
            medal = medals.get(i, f"{i+1}.")
            lines.append(f"{medal} {nick} — {int(score):,} ₽".replace(",", " "))

        await self.send_to_announcements("\n".join(lines))

    async def announce_fight_result(
        self, winner_name: str, loser_name: str, zone_name: str
    ) -> None:
        """Анонс результата драки за зону."""
        msg = (
            f"🤖 <b>Е-Байк Бот</b>\n\n"
            f"💀 <b>ДРАКА ЗА ЗОНУ!</b>\n\n"
            f"«{winner_name}» победил «{loser_name}» в бою за {zone_name}!\n"
            f"{zone_name} теперь под контролем «{winner_name}» на 24 часа.\n\n"
            f"Поздравляем победителя! 🏆"
        )
        await self.send_to_announcements(msg)

    async def announce_new_legend(self, player_name: str) -> None:
        """Анонс о достижении легендарного уровня."""
        msg = (
            f"🤖 <b>Е-Байк Бот</b>\n\n"
            f"👑 <b>НОВАЯ ЛЕГЕНДА!</b>\n\n"
            f"«{player_name}» достиг 6 уровня — Легенда!\n"
            f"Теперь ему доступны Чёрный рынок и Элитные клиенты.\n\n"
            f"Уважайте легенду! 🫡"
        )
        await self.send_to_general(msg)

    async def announce_global_event(self, event_name: str, event_description: str) -> None:
        """Анонс глобального события."""
        msg = (
            f"🤖 <b>Е-Байк Бот</b>\n\n"
            f"🌍 <b>ГЛОБАЛЬНОЕ СОБЫТИЕ</b>\n\n"
            f"<b>{event_name}</b>\n"
            f"{event_description}\n\n"
            f"Адаптируйтесь и зарабатывайте! 💰"
        )
        await self.send_to_announcements(msg)

    async def announce_patrol_info(self, user_name: str, zone: str, status: str) -> None:
        """Анонс информации о патруле от игрока."""
        emoji = {"тихо": "🟢", "обычно": "🟡", "рейд": "🟠", "облава": "🔴"}
        msg = (
            f"🤖 <b>Е-Байк Бот</b>\n\n"
            f"👮 <b>ПАТРУЛИ:</b> {emoji.get(status, '🟡')} {zone} — {status.upper()}\n"
            f"Информация от: {user_name}\n"
            f"+50 XP за помощь сообществу!"
        )
        await self.send_to_announcements(msg)


chat_integration: Optional[ChatIntegration] = None


def init_chat_integration(
    bot: Bot,
    general_chat_id: Optional[int] = None,
    announcements_chat_id: Optional[int] = None,
) -> ChatIntegration:
    """Инициализирует интеграцию с чатом."""
    global chat_integration
    chat_integration = ChatIntegration(
        bot=bot,
        general_chat_id=general_chat_id,
        announcements_chat_id=announcements_chat_id,
    )
    return chat_integration