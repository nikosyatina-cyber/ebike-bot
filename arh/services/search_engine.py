import aiohttp
import re
import logging
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)
ua = UserAgent()


async def search_all(query: str):
    """Поиск товаров через Яндекс.Маркет"""

    # Кодируем запрос
    search_query = query.replace(" ", "+")

    # Поиск на Яндекс.Маркете
    url = f"https://market.yandex.ru/search?text={search_query}&cvredirect=1"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as response:
                if response.status != 200:
                    logger.error(f"Yandex status {response.status}")
                    return await search_google(query)
                html = await response.text()

        products = []

        # Ищем блоки с товарами
        # Шаблоны для поиска
        patterns = [
            r'<article[^>]*data-autotest-id="product-snippet"[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*organic[^"]*"[^>]*>(.*?)</div>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches[:5]:
                # Извлекаем название
                title_match = re.search(r'<h3[^>]*>(.*?)</h3>', match)
                title = title_match.group(1) if title_match else ""
                title = re.sub(r'<[^>]+>', '', title).strip()

                # Извлекаем цену
                price_match = re.search(r'(\d+[\s]?\d*)\s?₽', match)
                price = 0
                if price_match:
                    price_str = price_match.group(1).replace(" ", "")
                    price = int(price_str) if price_str.isdigit() else 0

                # Извлекаем ссылку
                link_match = re.search(r'href="([^"]+)"', match)
                link = link_match.group(1) if link_match else ""

                if title and len(title) > 10:
                    # Определяем маркетплейс
                    marketplace = "Яндекс.Маркет"
                    if "ozon" in link.lower():
                        marketplace = "Ozon"
                    elif "wildberries" in link.lower() or "wb" in link.lower():
                        marketplace = "Wildberries"
                    elif "aliexpress" in link.lower():
                        marketplace = "AliExpress"

                    products.append({
                        "title": title[:80],
                        "price": price,
                        "marketplace": marketplace,
                        "url": link if link.startswith("http") else f"https://market.yandex.ru{link}"
                    })

            if products:
                break

        if products:
            return products

        return await search_google(query)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return await search_google(query)


async def search_google(query: str):
    """Поиск через Google Shopping"""

    url = "https://www.google.com/search"

    params = {
        "q": query,
        "tbm": "shop",
        "hl": "ru",
        "cr": "countryRU"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=20) as response:
                if response.status != 200:
                    return []
                html = await response.text()

        products = []

        # Поиск результатов
        product_blocks = re.findall(r'<div[^>]*class="[^"]*sh-osd__product-title[^"]*"[^>]*>(.*?)</div>', html)
        price_blocks = re.findall(r'<span[^>]*class="[^"]*a8Pemb[^"]*"[^>]*>(.*?)</span>', html)

        for i, block in enumerate(product_blocks[:5]):
            title = re.sub(r'<[^>]+>', '', block).strip()

            price = 0
            if i < len(price_blocks):
                price_text = re.sub(r'<[^>]+>', '', price_blocks[i]).strip()
                price_match = re.search(r'(\d+[\s]?\d*)', price_text)
                if price_match:
                    price = int(price_match.group(1).replace(" ", ""))

            if title:
                products.append({
                    "title": title[:80],
                    "price": price,
                    "marketplace": "Google Shopping",
                    "url": f"https://www.google.com/search?q={query.replace(' ', '+')}&tbm=shop"
                })

        return products

    except Exception as e:
        logger.error(f"Google error: {e}")
        return []