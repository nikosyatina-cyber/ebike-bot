from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from database.models import Platform, UserLevel
from bot.fsm.states import GameStates
from bot.keyboards.platforms import get_platform_keyboard, get_order_actions_keyboard


router = Router()

INFO = {
    Platform.YANDEX: (
        "🟡 <b>Яндекс.Еда</b>\n"
        "├── Оплата: Средняя + погода\n"
        "├── Штрафы: За опоздания\n"
        "└── Особенность: x1.8 в дождь"
    ),
    Platform.DOSTAVISTA: (
        "🔴 <b>Достависта</b>\n"
        "├── Оплата: Хаотичная (торг)\n"
        "├── Штрафы: Блокировка\n"
        "└── Особенность: Аукцион"
    ),
    Platform.X5: (
        "🟢 <b>Х5</b>\n"
        "├── Оплата: Высокая\n"
        "├── Штрафы: Слет слота -1500₽\n"
        "└── Особенность: Плановый слот + Биржа"
    ),
    Platform.MAGNIT: (
        "🟡 <b>Магнит</b>\n"
        "├── Оплата: Хорошая\n"
        "└── Особенность: Тетрис, корп. чаевые"
    ),
    Platform.OZON: (
        "🔵 <b>Озон Фреш</b>\n"
        "├── Оплата: Очень высокая\n"
        "├── Штрафы: Опоздание -100₽\n"
        "└── Особенность: Ледяной бонус"
    ),
    Platform.WB: (
        "🟣 <b>WB Курьер</b>\n"
        "├── Оплата: Маленькая\n"
        "└── Особенность: Бронь за 3 сек"
    ),
    Platform.TOPGO: (
        "🟠 <b>TopGO</b>\n"
        "├── Оплата: Средняя\n"
        "└── Особенность: Кластер до 3 заказов"
    ),
    Platform.VKUSVILL: (
        "🟣 <b>ВкусВилл</b>\n"
        "├── Оплата: Низкая\n"
        "└── Особенность: Конвейер, без штрафов"
    ),
    Platform.BLACK_MARKET: (
        "🏴 <b>Чёрный рынок</b>\n"
        "├── Оплата: Очень высокая\n"
        "└── Особенность: Конспирация"
    ),
    Platform.ELITE: (
        "👔 <b>Элитные клиенты</b>\n"
        "├── Оплата: Огромная\n"
        "└── Особенность: Капризы"
    ),
}

REQ = {
    Platform.YANDEX: UserLevel.STAGER,
    Platform.DOSTAVISTA: UserLevel.STAGER,
    Platform.X5: UserLevel.BEGINNER,
    Platform.MAGNIT: UserLevel.BEGINNER,
    Platform.OZON: UserLevel.RACER,
    Platform.WB: UserLevel.RACER,
    Platform.TOPGO: UserLevel.EXPERIENCED,
    Platform.VKUSVILL: UserLevel.ELITE,
    Platform.BLACK_MARKET: UserLevel.LEGEND,
    Platform.ELITE: UserLevel.LEGEND,
}


@router.callback_query(F.data.startswith("platform:"))
async def on_platform(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Обработчик выбора платформы."""
    await callback.answer()

    ps = callback.data.split(":")[1]
    user_crud = UserCRUD(session)
    user = await user_crud.get(callback.from_user.id)

    if user is None:
        await callback.message.answer("❌ Профиль не найден. Используйте /start.")
        return

    try:
        p = Platform(ps)
    except ValueError:
        await callback.message.answer("❌ Неизвестная платформа.")
        return

    if user.level.value < REQ[p].value:
        await callback.message.answer(
            f"❌ Платформа {p.value} доступна с уровня {REQ[p].name}."
        )
        return

    await user_crud.set_platform(callback.from_user.id, p)
    await state.update_data(platform=ps)

    await callback.message.edit_text(
        f"{INFO.get(p, 'Нет описания.')}\n\n"
        f"💰 Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"🔋 Заряд: <b>{user.battery_charge}%</b>\n\n"
        f"Искать заказы?",
        reply_markup=get_order_actions_keyboard(),
        parse_mode="HTML",
    )

    await state.set_state(GameStates.VIEWING_ORDERS)


@router.callback_query(F.data == "back_to_platforms")
async def back_platforms(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Возврат к выбору платформы."""
    await callback.answer()

    user_crud = UserCRUD(session)
    user = await user_crud.get(callback.from_user.id)

    if user is None:
        return

    await state.set_state(GameStates.CHOOSING_PLATFORM)
    await callback.message.edit_text(
        "📋 <b>Выберите платформу для работы:</b>",
        reply_markup=get_platform_keyboard(user.level),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "back_to_menu")
async def back_menu(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Возврат в главное меню."""
    await callback.answer()
    await state.clear()

    user_crud = UserCRUD(session)
    user = await user_crud.get(callback.from_user.id)

    if user is None:
        await callback.message.answer(
            "🚴 <b>Главное меню</b>\n\n"
            "Используйте команды:\n"
            "/orders — заказы\n"
            "/garage — гараж\n"
            "/stats — профиль\n"
            "/rating — рейтинг\n"
            "/faq — справка",
            parse_mode="HTML",
        )
        return

    level_names = {
        1: "🥚 Стажёр", 2: "🐣 Подаван", 3: "🦊 Гонщик",
        4: "🐺 Матёрый", 5: "🦅 Элита", 6: "👑 Легенда",
    }

    display_name = f"@{user.username}" if user.username else user.full_name

    await callback.message.answer(
        f"🚴 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
        f"👤 {display_name}\n"
        f"⭐ Уровень: {level_names.get(user.level.value, '?')}\n"
        f"💰 Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"🔋 Заряд: <b>{user.battery_charge}%</b>\n"
        f"📊 Репутация: <b>{user.reputation}/100</b>\n\n"
        f"Используйте команды:\n"
        f"/orders — заказы\n"
        f"/garage — гараж\n"
        f"/stats — профиль\n"
        f"/rating — рейтинг\n"
        f"/faq — справка",
        parse_mode="HTML",
    )