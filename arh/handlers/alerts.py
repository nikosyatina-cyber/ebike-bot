from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from arh.database import add_alert, get_user_alerts, deactivate_alert

router = Router()


@router.message(Command("watch"))
async def watch_command(message: Message):
    args = message.text.split()

    if len(args) < 3:
        await message.answer("🔔 Пример: /watch контроллер 5000")
        return

    keyword = args[1]
    try:
        price = int(args[2])
    except:
        await message.answer("❌ Цена должна быть числом")
        return

    await add_alert(message.from_user.id, keyword, price)
    await message.answer(f"✅ Алерт: {keyword} до {price} ₽")


@router.message(Command("my_alerts"))
async def my_alerts_command(message: Message):
    alerts = await get_user_alerts(message.from_user.id)

    if not alerts:
        await message.answer("🔔 Нет алертов")
        return

    text = "🔔 Ваши алерты:\n\n"
    for a in alerts:
        text += f"ID: {a[0]} - {a[1]} - {a[2]} ₽\n"
    text += "\n/del_alert ID - удалить"
    await message.answer(text)


@router.message(Command("del_alert"))
async def del_alert_command(message: Message):
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ /del_alert ID")
        return

    try:
        alert_id = int(args[1])
        await deactivate_alert(alert_id)
        await message.answer(f"✅ Алерт #{alert_id} удален")
    except:
        await message.answer("❌ Неверный ID")