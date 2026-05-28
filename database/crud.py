from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.models import User, UserLevel, TransportType, Platform


class UserCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, username: Optional[str] = None, full_name: str = "Курьер") -> User:
        """Получить пользователя или создать нового."""
        # Сначала ищем существующего
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is not None:
            # Обновляем username и full_name если изменились
            if username and user.username != username:
                user.username = username
            if full_name and user.full_name != full_name and user.full_name == "Курьер":
                user.full_name = full_name
            await self.session.commit()
            return user

        # Создаём нового
        user = User(
            id=user_id,
            username=username,
            full_name=full_name or "Курьер",
        )
        self.session.add(user)
        try:
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Создан новый игрок: {user}")
        except Exception as e:
            await self.session.rollback()
            # Если другой поток уже создал — просто получаем
            result = await self.session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user is None:
                raise e
        return user

    async def get(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def add_xp(self, user_id: int, amount: int) -> Optional[int]:
        user = await self.get(user_id)
        if user is None:
            return None
        user.xp += amount
        new_level = self._calculate_level(user.xp)
        if new_level > user.level:
            user.level = new_level
            logger.info(f"Игрок {user_id} повысил уровень до {new_level.name}")
        await self.session.commit()
        return user.xp

    async def add_balance(self, user_id: int, amount: float) -> Optional[float]:
        user = await self.get(user_id)
        if user is None:
            return None
        user.balance += amount
        await self.session.commit()
        return user.balance

    async def set_platform(self, user_id: int, platform: Platform) -> bool:
        user = await self.get(user_id)
        if user is None:
            return False
        user.current_platform = platform
        await self.session.commit()
        return True

    async def set_transport(self, user_id: int, transport: TransportType) -> bool:
        user = await self.get(user_id)
        if user is None:
            return False
        user.current_transport = transport
        await self.session.commit()
        return True

    async def update_battery(self, user_id: int, charge: int) -> bool:
        user = await self.get(user_id)
        if user is None:
            return False
        user.battery_charge = max(0, min(100, charge))
        await self.session.commit()
        return True

    @staticmethod
    def _calculate_level(xp: int) -> UserLevel:
        if xp >= 7000:
            return UserLevel.LEGEND
        elif xp >= 4500:
            return UserLevel.ELITE
        elif xp >= 2000:
            return UserLevel.EXPERIENCED
        elif xp >= 800:
            return UserLevel.RACER
        elif xp >= 250:
            return UserLevel.BEGINNER
        else:
            return UserLevel.STAGER

    @staticmethod
    def get_xp_for_next_level(current_level: UserLevel) -> int:
        thresholds = {
            UserLevel.STAGER: 250,
            UserLevel.BEGINNER: 800,
            UserLevel.RACER: 2000,
            UserLevel.EXPERIENCED: 4500,
            UserLevel.ELITE: 7000,
            UserLevel.LEGEND: float("inf"),
        }
        return thresholds.get(current_level, 0)