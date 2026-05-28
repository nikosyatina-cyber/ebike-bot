from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from arh.services.search_engine import search_all

router = Router()


@router.message(Command("market"))
async def market_command(message: Message):
    query = message.text.replace("/market", "").strip()

    if not query:
        await message.answer(
            "🔍 <b>Поиск на маркетплейсах</b>\n\n"
            "Пример: /market контроллер 48v\n"
            "Пример: /market аккумулятор 18650\n"
            "Пример: /market двигатель"
        )
        return

    status_msg = await message.answer(f"🔍 Ищу <b>{query}</b> на Яндекс.Маркете...")

    products = await search_all(query)

    await status_msg.delete()

    if not products:
        await message.answer(
            f"😔 По запросу <b>{query}</b> ничего не найдено\n\n"
            f"💡 <b>Советы:</b>\n"
            f"• Используйте короткие запросы\n"
            f"• Пример: /market контроллер\n"
            f"• Пример: /market аккумулятор 18650\n\n"
            f"🔗 <b>Прямые ссылки:</b>\n"
            f"🛒 <a href='https://www.ozon.ru/search/?text={query}'>Поиск на Ozon</a>\n"
            f"🟣 <a href='https://www.wildberries.ru/catalog/0/search.aspx?search={query}'>Поиск на Wildberries</a>"
        )
        return

    text = f"🛒 <b>Результаты поиска: {query}</b>\n\n"

    for i, product in enumerate(products[:5], 1):
        price_str = f"{product['price']:,} ₽" if product['price'] > 0 else "Цена не указана"

        text += (
            f"{i}. <b>{product['title'][:60]}</b>\n"
            f"   💰 {price_str}\n"
            f"   🏪 {product['marketplace']}\n"
            f"   🔗 <a href='{product['url']}'>Перейти к товару</a>\n\n"
        )

    # Добавляем прямые ссылки для поиска
    text += f"\n🔍 <b>Поискать самостоятельно:</b>\n"
    text += f"🛒 <a href='https://www.ozon.ru/search/?text={query}'>Ozon</a> | "
    text += f"🟣 <a href='https://www.wildberries.ru/catalog/0/search.aspx?search={query}'>Wildberries</a>"

    await message.answer(text, disable_web_page_preview=False)