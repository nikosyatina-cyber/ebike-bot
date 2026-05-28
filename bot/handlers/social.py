import random

from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud import UserCRUD
from database.models import InventoryItem
from database.engine import cache


router = Router()


@router.message(Command("передать"))
async def cmd_transfer(
    message: types.Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Передать предмет другому игроку."""
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("❌ Использование: /передать @игрок [предмет]")
        return

    recipient_str = args[0]
    item_name = " ".join(args[1:])

    if not recipient_str.startswith("@"):
        await message.answer("❌ Укажите получателя через @username")
        return

    result = await session.execute(
        select(InventoryItem).where(
            InventoryItem.user_id == message.from_user.id,
            InventoryItem.item_name == item_name,
        )
    )
    item = result.scalar_one_or_none()

    if item is None:
        await message.answer(f"❌ У вас нет предмета «{item_name}»")
        return

    if item.quantity > 1:
        item.quantity -= 1
    else:
        await session.delete(item)

    await session.commit()

    await message.answer(
        f"📦 <b>ПЕРЕДАЧА</b>\n\n"
        f"Предмет «{item_name}» передан {recipient_str}!\n\n"
        f"{recipient_str}, используйте /принять @{message.from_user.username} {item_name}",
        parse_mode="HTML",
    )


@router.message(Command("принять"))
async def cmd_accept(
    message: types.Message,
    command: CommandObject,
    session: AsyncSession,
) -> None:
    """Принять предмет."""
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.answer("❌ Использование: /принять @отправитель [предмет]")
        return

    item_name = " ".join(args[1:])

    result = await session.execute(
        select(InventoryItem).where(
            InventoryItem.user_id == message.from_user.id,
            InventoryItem.item_name == item_name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.quantity += 1
    else:
        new_item = InventoryItem(
            user_id=message.from_user.id,
            item_name=item_name,
            quantity=1,
        )
        session.add(new_item)

    await session.commit()

    await message.answer(
        f"✅ <b>ПРИНЯТО!</b>\n\n"
        f"Предмет «{item_name}» получен от {args[0]}.",
        parse_mode="HTML",
    )


@router.message(Command("рейтинг"))
async def cmd_rating(message: types.Message) -> None:
    """Показать текущий рейтинг дня."""
    from datetime import datetime

    today = datetime.now().strftime('%Y-%m-%d')
    top_data = await cache.zrevrange(f"ratings:daily:{today}", 0, 9)

    if not top_data:
        await message.answer("🏆 Рейтинг дня пока пуст. Выполняйте заказы!")
        return

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    lines = ["🏆 <b>ТОП-10 ЗА СЕГОДНЯ</b>\n"]

    for i, (member, score) in enumerate(top_data):
        nickname = member.split(":", 1)[1] if ":" in member else member
        medal = medals.get(i, f"{i+1}.")
        lines.append(f"{medal} {nickname} — {int(score):,} ₽".replace(",", " "))

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("улучшить"))
async def cmd_upgrade_skill(
    message: types.Message,
    command: CommandObject,
) -> None:
    """Улучшить навык."""
    from bot.handlers.skills import upgrade_skill, SKILLS

    args = command.args.split() if command.args else []
    if not args:
        skills_list = "\n".join([f"{v['name']} — {k}" for k, v in SKILLS.items()])
        await message.answer(
            f"❌ Использование: /улучшить [навык]\n\n"
            f"Доступные навыки:\n{skills_list}"
        )
        return

    skill_name = args[0].lower()

    skill_id = None
    for sid, sdata in SKILLS.items():
        if skill_name in sid or skill_name in sdata['name'].lower():
            skill_id = sid
            break

    if skill_id is None:
        await message.answer("❌ Неизвестный навык.")
        return

    success, msg = await upgrade_skill(message.from_user.id, skill_id)
    await message.answer(msg)


@router.message(Command("права"))
async def cmd_license(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Получить права категории М."""
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)
    if user is None:
        return

    if user.level.value < 5:
        await message.answer("❌ Права категории «М» доступны с 5 уровня (Элита).")
        return

    already_has = await cache.get(f"user:{user.id}:license_m")
    if already_has:
        await message.answer("✅ У вас уже есть права категории «М».")
        return

    cost = 2500
    if user.balance < cost:
        await message.answer(f"❌ Недостаточно средств! Нужно {cost} ₽")
        return

    questions = [
        {"q": "Можно ли ездить на красный свет?", "a": "нет"},
        {"q": "Нужен ли шлем на электроскутере?", "a": "да"},
        {"q": "Можно ли возить пассажиров на багажнике?", "a": "нет"},
        {"q": "Разрешён ли тюнинг до 5000W с правами М?", "a": "да"},
        {"q": "Нужно ли уступать пешеходам на переходе?", "a": "да"},
    ]

    question = random.choice(questions)

    await cache.set(
        f"user:{user.id}:license_test",
        {"question": question, "attempts": 1},
        expire_seconds=300,
    )

    await message.answer(
        f"📝 <b>ТЕСТ НА ПРАВА КАТЕГОРИИ «М»</b>\n\n"
        f"Вопрос: {question['q']}\n\n"
        f"Ответьте «да» или «нет».\n"
        f"Стоимость попытки: {cost} ₽"
    )


@router.message(F.text.lower().isin(["да", "нет"]))
async def check_license_answer(
    message: types.Message,
    session: AsyncSession,
) -> None:
    """Проверка ответа на тест прав."""
    user_id = message.from_user.id
    test_data = await cache.get(f"user:{user_id}:license_test")

    if test_data is None:
        return

    question = test_data["question"]
    answer = message.text.lower().strip()

    if answer == question["a"]:
        user_crud = UserCRUD(session)
        user = await user_crud.get(user_id)
        if user:
            await user_crud.add_balance(user_id, -2500)

        await cache.set(f"user:{user_id}:license_m", True)
        await cache.delete(f"user:{user_id}:license_test")

        await message.answer(
            "✅ <b>ПОЗДРАВЛЯЕМ!</b>\n\n"
            "Вы получили права категории «М»!\n"
            "Теперь можно легально ездить на моторах до 5000W.\n"
            "Мотобат не будет тормозить без повода.",
            parse_mode="HTML",
        )
    else:
        await cache.delete(f"user:{user_id}:license_test")
        await message.answer(
            f"❌ Неверно! Правильный ответ: <b>{question['a'].upper()}</b>\n"
            f"Попробуйте снова через час.",
            parse_mode="HTML",
        )

        # Английские алиасы команд (для меню бота)
        @router.message(Command("rating"))
        async def cmd_rating_en(message: types.Message):
            """Алиас для /рейтинг."""
            await cmd_rating(message)

        @router.message(Command("profile"))
        async def cmd_profile_en(message: types.Message, session: AsyncSession):
            """Алиас для /профиль."""
            from database.crud import UserCRUD
            user_crud = UserCRUD(session)
            user = await user_crud.get(message.from_user.id)
            if user:
                level_names = {
                    1: "🥚 Стажёр", 2: "🐣 Подаван", 3: "🦊 Гонщик",
                    4: "🐺 Матёрый", 5: "🦅 Элита", 6: "👑 Легенда",
                }
                await message.answer(
                    f"📊 <b>ПРОФИЛЬ</b>\n"
                    f"├── Уровень: <b>{level_names.get(user.level.value, '?')}</b>\n"
                    f"├── Опыт: <b>{user.xp} XP</b>\n"
                    f"├── Баланс: <b>{user.balance:.0f} ₽</b>\n"
                    f"├── Заряд: <b>{user.battery_charge}%</b>\n"
                    f"└── Репутация: <b>{user.reputation}/100</b>",
                    parse_mode="HTML",
                )

        @router.message(Command("zones"))
        async def cmd_zones_en(message: types.Message, session: AsyncSession):
            """Алиас для /зоны."""
            await cmd_zones_group(message, session)

        # Импорт для алиаса
        from bot.handlers.group import cmd_zones_group