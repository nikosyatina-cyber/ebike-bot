import json
import time
from typing import Optional, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from loguru import logger

from core.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_size=20,
    max_overflow=40,
    pool_timeout=60,
    pool_recycle=3600,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Ошибка сессии БД: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(f"Подключение к SQLite успешно: {settings.db_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка подключения к SQLite: {e}")
        return False


async def create_tables() -> None:
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы созданы")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Соединения с SQLite закрыты")


class CacheManager:
    _instance: Optional["CacheManager"] = None
    _memory_cache: dict = {}

    def __new__(cls) -> "CacheManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._memory_cache = {}
        return cls._instance

    async def init_tables(self) -> None:
        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL
                )
            """))

    async def set(self, key: str, value: Any, expire_seconds: int = None) -> None:
        self._memory_cache[key] = value
        expires_at = (time.time() + expire_seconds) if expire_seconds else None
        async with async_session() as session:
            await session.execute(
                text("INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (:key, :value, :expires_at)"),
                {"key": key, "value": json.dumps(value, ensure_ascii=False, default=str), "expires_at": expires_at},
            )
            await session.commit()

    async def get(self, key: str) -> Optional[Any]:
        if key in self._memory_cache:
            return self._memory_cache[key]
        async with async_session() as session:
            result = await session.execute(
                text("SELECT value, expires_at FROM cache WHERE key = :key"),
                {"key": key},
            )
            row = result.fetchone()
            if row is None:
                return None
            value_str, expires_at = row
            if expires_at is not None and time.time() > expires_at:
                await self.delete(key)
                return None
            return json.loads(value_str)

    async def delete(self, key: str) -> None:
        self._memory_cache.pop(key, None)
        async with async_session() as session:
            await session.execute(text("DELETE FROM cache WHERE key = :key"), {"key": key})
            await session.commit()

    async def zadd(self, key: str, score: float, member: str) -> None:
        data = await self.get(key) or {}
        data[member] = score
        await self.set(key, data)

    async def zincrby(self, key: str, amount: float, member: str) -> None:
        data = await self.get(key) or {}
        data[member] = data.get(member, 0) + amount
        await self.set(key, data)

    async def zrevrange(self, key: str, start: int, stop: int) -> list:
        data = await self.get(key) or {}
        sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[start:stop + 1]

    async def keys(self, pattern: str = "*") -> list:
        async with async_session() as session:
            result = await session.execute(
                text("SELECT key FROM cache WHERE key LIKE :pattern"),
                {"pattern": pattern.replace("*", "%")},
            )
            return [row[0] for row in result.fetchall()]

    async def exists(self, key: str) -> bool:
        value = await self.get(key)
        return value is not None

    async def hgetall(self, key: str) -> dict:
        data = await self.get(key)
        if isinstance(data, dict):
            return data
        return {}

    async def hset(self, key: str, field: str, value: Any) -> None:
        data = await self.get(key) or {}
        data[field] = value
        await self.set(key, data)


cache = CacheManager()
