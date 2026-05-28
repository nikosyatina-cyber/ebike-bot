from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.crud import UserCRUD
from database.models import UserLevel
from database.engine import cache
from bot.fsm.states import GameStates
from bot.keyboards.platforms import get_platform_keyboard
from bot.keyboards.garage import get_garage_main_keyboard


router = Router()


def format_profile(user) -> str:
    level_names = {
        UserLevel.STAGER: "🥚 Стажёр",
        UserLevel.BEGINNER: "🐣 Подаван",
        UserLevel.RACER: "🦊 Гонщик",
        UserLevel.EXPERIENCED: "🐺 Матёрый",
        UserLevel.ELITE: "🦅 Элита",
        UserLevel.LEGEND: "👑 Легенда",
    }
    display_name = f"@{user.username}" if user.username else user.full_name
    return (
        f"👤 <b>{display_name}</b>\n\n"
        f"📊 <b>ПРОФИЛЬ</b>\n"
        f"├── Уровень: <b>{level_names.get(user.level, '?')}</b>\n"
        f"├── Опыт: <b>{user.xp} XP</b>\n"
        f"├── Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"├── Заряд: <b>{user.battery_charge}%</b>\n"
        f"└── Репутация: <b>{user.reputation}/100</b>"
    )


@router.message(Command("orders"))
@router.message(Command("заказы"))
async def cmd_orders(message: types.Message, state: FSMContext, session: AsyncSession):
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)
    if user is None or user.is_banned:
        await message.reply("❌ Профиль не найден. Используйте /start")
        return

    # Проверяем, есть ли активный заказ
    data = await state.get_data()
    current_state = await state.get_state()
    co = data.get("current_order")

    # Если заказ в процессе доставки — не даём новый
    if current_state in [
        GameStates.RIDING_TO_RESTAURANT,
        GameStates.RIDING_TO_CLIENT,
        GameStates.PATROL_ENCOUNTER,
    ]:
        await message.reply(
            "🚴 <b>У вас уже есть активный заказ!</b>\n\n"
            "Дождитесь завершения текущей доставки.",
            parse_mode="HTML",
        )
        return

    # Если есть ожидающий заказ, но не в пути — можно выбрать новый
    await state.clear()
    await state.set_state(GameStates.CHOOSING_PLATFORM)

    await message.reply(
        format_profile(user) + "\n\n<b>Выберите платформу:</b>",
        reply_markup=get_platform_keyboard(user.level),
        parse_mode="HTML",
    )


@router.message(Command("stats"))
@router.message(Command("profile"))
@router.message(Command("me"))
@router.message(Command("стата"))
@router.message(Command("профиль"))
async def cmd_stats(message: types.Message, session: AsyncSession):
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)
    if user is None:
        await message.reply("❌ Профиль не найден. Используйте /start")
        return
    await message.reply(format_profile(user), parse_mode="HTML")


@router.message(Command("rating"))
@router.message(Command("top"))
@router.message(Command("рейтинг"))
@router.message(Command("топ"))
async def cmd_rating(message: types.Message, session: AsyncSession):
    today = datetime.now().strftime('%Y-%m-%d')
    top_data = await cache.zrevrange(f"ratings:daily:{today}", 0, 9)

    if not top_data:
        await message.reply("🏆 <b>РЕЙТИНГ ДНЯ</b>\n\nПока никто не выполнил заказов.\nСтаньте первым! 🚀", parse_mode="HTML")
        return

    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)
    user_place = -1

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    display_name = f"@{user.username}" if user and user.username else (user.full_name if user else "Вы")
    lines = [f"👤 <b>{display_name}</b>\n\n🏆 <b>ТОП-10 ЗА СЕГОДНЯ</b>\n"]

    for i, (member, score) in enumerate(top_data):
        user_id_str = member.split(":")[0]
        nickname = member.split(":", 1)[1] if ":" in member else member
        medal = medals.get(i, f"{i+1}.")
        lines.append(f"{medal} {nickname} — {int(score):,} ₽".replace(",", " "))
        if user and str(user.id) == user_id_str:
            user_place = i + 1

    if user and user_place == -1:
        lines.append(f"\n📌 Ваше место: пока не в топ-10")
    elif user and user_place > 0:
        lines.append(f"\n📌 Ваше место: <b>{user_place}</b>")

    lines.append("\n🎁 <b>Награды дня:</b>")
    lines.append("🥇 +300 XP | 🥈 +200 XP | 🥉 +100 XP")

    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(F.text == "🎯 Навыки")
async def cmd_skills(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Показывает навыки персонажа."""
    from bot.handlers.skills import get_skills, format_skills, SKILL_XP_COST

    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)
    if user is None:
        return

    skills = await get_skills(message.from_user.id)
    text = format_skills(skills)
    text += f"\n💰 Баланс: {user.balance:.0f} ₽\n"
    text += "\n<b>Для улучшения:</b> /улучшить [навык]"

    await message.reply(text, parse_mode="HTML")


@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Обработчик кнопки 'Настройки'."""
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)

    if user is None:
        await message.reply("❌ Профиль не найден. Используйте /start.")
        return

    await message.reply(
        "⚙️ <b>НАСТРОЙКИ</b>\n\n"
        "Раздел в разработке.\n\n"
        "Пока здесь можно только вернуться в главное меню.",
        parse_mode="HTML",
    )