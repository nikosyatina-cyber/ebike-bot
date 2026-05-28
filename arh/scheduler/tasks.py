import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from arh.database import get_all_active_alerts
from arh.services.search_engine import search_all

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def check_prices(bot):
    logger.info("🔄 Проверка цен...")
    alerts = await get_all_active_alerts()

    for alert in alerts:
        alert_id, user_id, keyword, target_price = alert
        products = await search_all(keyword)

        for product in products:
            if product.get("price", 0) <= target_price:
                text = f"🔥 Цена снизилась!\n📦 {product['title']}\n💰 {product['price']} ₽\n🔗 {product['url']}"
                await bot.send_message(user_id, text, disable_web_page_preview=True)
                break


def start_scheduler(bot):
    scheduler.add_job(check_prices, "interval", minutes=30, args=[bot])
    scheduler.start()
    logger.info("⏰ Планировщик запущен")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Планировщик остановлен")