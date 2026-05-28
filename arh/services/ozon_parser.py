import aiohttp
import logging
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)
ua = UserAgent()

async def search_ozon(query: str):
    """Поиск на Ozon через прямую ссылку"""
    return []