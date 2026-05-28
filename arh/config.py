import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = os.getenv("DB_NAME", "electrohub.db")

# XP система
XP_COOLDOWN = 30  # секунд
XP_PER_MESSAGE = 1

# Карма
KARMA_AMOUNT = 5
KARMA_COOLDOWN = 60  # секунд

# Парсеры
CHECK_PRICES_INTERVAL = 30  # минут
SEARCH_RESULTS_LIMIT = 5