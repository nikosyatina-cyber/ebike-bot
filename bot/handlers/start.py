from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database.crud import UserCRUD


router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: types.Message,
    state: FSMContext,
    session,
) -> None:
    await state.clear()

    user_crud = UserCRUD(session)
    user = await user_crud.get_or_create(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name or "Курьер",
    )

    level_names = {
        1: "🥚 Стажёр", 2: "🐣 Подаван", 3: "🦊 Гонщик",
        4: "🐺 Матёрый", 5: "🦅 Элита", 6: "👑 Легенда",
    }

    await message.reply(
        f"🚴 <b>Добро пожаловать, {user.full_name}!</b>\n\n"
        f"⭐ Уровень: <b>{level_names.get(user.level.value, '?')}</b>\n"
        f"💰 Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"🔋 Заряд: <b>{user.battery_charge}%</b>\n\n"
        f"📋 <b>Доступные команды:</b>\n"
        f"/orders — взять заказ\n"
        f"/garage — гараж и транспорт\n"
        f"/map — зоны города\n"
        f"/stats — ваш профиль\n"
        f"/rating — топ дня\n"
        f"/skills — навыки\n"
        f"/quests — ежедневные задания\n"
        f"/achievements — достижения\n"
        f"/business — ваш бизнес\n"
        f"/blackmarket — чёрный рынок\n"
        f"/faq — справка\n\n"
        f"Начните с /orders чтобы взять первый заказ!",
        parse_mode="HTML",
    )