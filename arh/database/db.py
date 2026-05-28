import aiosqlite
from arh.config import DB_NAME

_db = None


async def get_db():
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_NAME)
        _db.row_factory = aiosqlite.Row
    return _db


async def init_db():
    db = await get_db()

    # Таблица пользователей
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            xp INTEGER DEFAULT 0,
            karma INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            messages_count INTEGER DEFAULT 0,
            last_message_time INTEGER DEFAULT 0,
            last_karma_time INTEGER DEFAULT 0
        )
    """)

    # Таблица алертов
    await db.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            keyword TEXT,
            target_price INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    """)

    # Индексы
    await db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON alerts(user_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_keyword ON alerts(keyword)")

    await db.commit()
    print("✅ База данных инициализирована")


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None