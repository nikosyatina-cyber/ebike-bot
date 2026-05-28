import time
from arh.config import XP_COOLDOWN, KARMA_COOLDOWN

def can_get_xp(last_message_time: int):
    now = int(time.time())
    if now - last_message_time >= XP_COOLDOWN:
        return True, 0
    return False, XP_COOLDOWN - (now - last_message_time)

def can_use_karma(last_karma_time: int):
    now = int(time.time())
    if now - last_karma_time >= KARMA_COOLDOWN:
        return True, 0
    return False, KARMA_COOLDOWN - (now - last_karma_time)