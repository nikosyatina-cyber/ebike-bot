import time
from arh.database.db import get_db

async def get_user(user_id: int):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return await cursor.fetchone()

async def create_user(user_id: int, username: str = None, first_name: str = None):
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name)
    )
    await db.commit()

async def add_xp(user_id: int, amount: int):
    db = await get_db()
    await db.execute(
        "UPDATE users SET xp = xp + ?, messages_count = messages_count + 1, last_message_time = ? WHERE user_id = ?",
        (amount, int(time.time()), user_id)
    )
    await db.execute(
        "UPDATE users SET level = 1 + (xp / 100) WHERE user_id = ?",
        (user_id,)
    )
    await db.commit()

async def add_karma(user_id: int, amount: int):
    db = await get_db()
    await db.execute(
        "UPDATE users SET karma = karma + ? WHERE user_id = ?",
        (amount, user_id)
    )
    await db.commit()

async def update_last_karma_time(user_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE users SET last_karma_time = ? WHERE user_id = ?",
        (int(time.time()), user_id)
    )
    await db.commit()

async def get_top_users(limit: int = 10):
    db = await get_db()
    cursor = await db.execute(
        "SELECT user_id, username, first_name, xp, karma, level, messages_count FROM users ORDER BY xp DESC LIMIT ?",
        (limit,)
    )
    return await cursor.fetchall()

async def add_alert(user_id: int, keyword: str, target_price: int):
    db = await get_db()
    await db.execute(
        "INSERT INTO alerts (user_id, keyword, target_price) VALUES (?, ?, ?)",
        (user_id, keyword.lower(), target_price)
    )
    await db.commit()

async def get_user_alerts(user_id: int):
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, keyword, target_price FROM alerts WHERE user_id = ? AND is_active = 1",
        (user_id,)
    )
    return await cursor.fetchall()

async def get_all_active_alerts():
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, user_id, keyword, target_price FROM alerts WHERE is_active = 1"
    )
    return await cursor.fetchall()

async def deactivate_alert(alert_id: int):
    db = await get_db()
    await db.execute(
        "UPDATE alerts SET is_active = 0 WHERE id = ?",
        (alert_id,)
    )
    await db.commit()