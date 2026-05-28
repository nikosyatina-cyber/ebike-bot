"""Обработчики для групповых чатов."""

from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatType
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.crud import UserCRUD
from database.models import User, UserLevel
from database.engine import cache
from bot.fsm.states import GameStates
from bot.keyboards.platforms import get_platform_keyboard, get_order_actions_keyboard
from bot.keyboards.garage import get_garage_main_keyboard


router = Router()


def is_group(chat_type: str) -> bool:
    return chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]


async def get_user(message: types.Message, session: AsyncSession):
    user_crud = UserCRUD(session)
    return await user_crud.get_or_create(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name or "Курьер",
    )


def format_profile(user: User) -> str:
    level_names = {
        1: "🥚 Стажёр", 2: "🐣 Подаван", 3: "🦊 Гонщик",
        4: "🐺 Матёрый", 5: "🦅 Элита", 6: "👑 Легенда",
    }
    display_name = f"@{user.username}" if user.username else user.full_name
    return (
        f"👤 <b>{display_name}</b>\n\n"
        f"📊 <b>ПРОФИЛЬ</b>\n"
        f"├── Уровень: <b>{level_names.get(user.level.value, '?')}</b>\n"
        f"├── Опыт: <b>{user.xp} XP</b>\n"
        f"├── Баланс: <b>{user.balance:.0f} ₽</b>\n"
        f"├── Заряд: <b>{user.battery_charge}%</b>\n"
        f"└── Репутация: <b>{user.reputation}/100</b>"
    )


@router.message(Command("start"))
async def cmd_start_group(message: types.Message, session: AsyncSession):
    if not is_group(message.chat.type):
        return
    await message.reply(
        "🚴 <b>Е-Байк: Доставка</b>\n\n"
        "Я — симулятор курьера! Играйте прямо в этом чате!\n\n"
        "/orders — взять заказ\n"
        "/garage — транспорт\n"
        "/map — зоны\n"
        "/stats — профиль\n"
        "/rating — топ\n"
        "/skills — навыки\n"
        "/achievements — достижения\n"
        "/faq — справка",
        parse_mode="HTML",
    )


@router.message(Command("orders"))
@router.message(Command("заказы"))
async def cmd_orders_group(message: types.Message, state: FSMContext, session: AsyncSession):
    user = await get_user(message, session)
    if user is None or user.is_banned:
        return

    # Проверяем, есть ли активный заказ
    current_state = await state.get_state()

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

    await state.clear()
    await state.set_state(GameStates.CHOOSING_PLATFORM)
    await state.update_data(chat_id=message.chat.id)

    await message.reply(
        format_profile(user) + "\n\n<b>Выберите платформу:</b>",
        reply_markup=get_platform_keyboard(user.level),
        parse_mode="HTML",
    )


@router.message(Command("garage"))
@router.message(Command("гараж"))
async def cmd_garage_group(message: types.Message, state: FSMContext, session: AsyncSession):
    from bot.handlers.garage import get_transport_display
    user = await get_user(message, session)
    if user is None:
        return
    await state.set_state(GameStates.GARAGE_MAIN)
    await state.update_data(chat_id=message.chat.id)
    transport_info = await get_transport_display(user, session)
    await message.reply(
        f"🔧 <b>ГАРАЖ</b>\n\n{transport_info}\n\nВыберите действие:",
        reply_markup=get_garage_main_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("map"))
@router.message(Command("zones"))
@router.message(Command("карта"))
@router.message(Command("зоны"))
async def cmd_map_group(message: types.Message, session: AsyncSession):
    from generators.zones import ZONES
    zc = await cache.hgetall("zones:control") or {}
    lines = ["🌍 <b>ЗОНЫ ГОРОДА</b>\n"]
    for zone_key, zone_data in ZONES.items():
        owner_id = zc.get(zone_key)
        if owner_id:
            try:
                user_crud = UserCRUD(session)
                owner = await user_crud.get(int(owner_id))
                owner_name = f"@{owner.username}" if owner and owner.username else (owner.full_name if owner else f"ID:{owner_id}")
            except:
                owner_name = str(owner_id)
        else:
            owner_name = "Свободна"
        lines.append(f"{zone_data['name']}\n├── Владелец: {owner_name}\n└── Бонус: {zone_data['bonus_description']}\n")
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("stats"))
@router.message(Command("profile"))
@router.message(Command("me"))
@router.message(Command("стата"))
@router.message(Command("профиль"))
async def cmd_stats_group(message: types.Message, session: AsyncSession):
    user = await get_user(message, session)
    if user is None:
        return
    await message.reply(format_profile(user), parse_mode="HTML")


@router.message(Command("rating"))
@router.message(Command("top"))
@router.message(Command("рейтинг"))
@router.message(Command("топ"))
async def cmd_rating_group(message: types.Message, session: AsyncSession):
    today = datetime.now().strftime('%Y-%m-%d')
    top_data = await cache.zrevrange(f"ratings:daily:{today}", 0, 9)
    if not top_data:
        await message.reply("🏆 <b>РЕЙТИНГ ДНЯ</b>\n\nПока никто не выполнил заказов.", parse_mode="HTML")
        return
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    limit = 5 if is_group(message.chat.type) else 10
    lines = [f"👤 <b>@{message.from_user.username or message.from_user.full_name}</b>\n\n🏆 <b>ТОП КУРЬЕРОВ ДНЯ</b>\n"]
    for i, (member, score) in enumerate(top_data[:limit]):
        nickname = member.split(":", 1)[1] if ":" in member else member
        medal = medals.get(i, f"{i+1}.")
        lines.append(f"{medal} {nickname} — {int(score):,} ₽".replace(",", " "))
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("skills"))
@router.message(Command("навыки"))
async def cmd_skills_group(message: types.Message, session: AsyncSession):
    from bot.handlers.skills import get_skills, format_skills
    user = await get_user(message, session)
    if user is None:
        return
    skills = await get_skills(message.from_user.id)
    text = format_skills(skills)
    text += f"\n💰 Баланс: {user.balance:.0f} ₽\n\n<b>Для улучшения:</b> /upgrade [навык]"
    await message.reply(text, parse_mode="HTML")


@router.message(Command("upgrade"))
@router.message(Command("улучшить"))
async def cmd_upgrade_group(message: types.Message, command: CommandObject):
    from bot.handlers.skills import upgrade_skill, SKILLS
    args = command.args.split() if command.args else []
    if not args:
        skills_list = "\n".join([f"{v['name']} — {k}" for k, v in SKILLS.items()])
        await message.reply(f"❌ /upgrade [навык]\n\n{skills_list}")
        return
    skill_name = args[0].lower()
    skill_id = None
    for sid, sdata in SKILLS.items():
        if skill_name in sid or skill_name in sdata['name'].lower():
            skill_id = sid
            break
    if skill_id is None:
        await message.reply("❌ Неизвестный навык.")
        return
    success, msg = await upgrade_skill(message.from_user.id, skill_id)
    await message.reply(msg)


@router.message(Command("achievements"))
@router.message(Command("achievs"))
@router.message(Command("ачивки"))
@router.message(Command("достижения"))
async def cmd_achievements_group(message: types.Message, session: AsyncSession):
    from bot.handlers.achievements import check_and_award_achievements, get_user_stats, ACHIEVEMENTS
    user_id = message.from_user.id
    await check_and_award_achievements(user_id, session)
    unlocked = await cache.get(f"user:{user_id}:achievements") or []
    if isinstance(unlocked, str):
        unlocked = []
    stats = await get_user_stats(user_id)
    user = await get_user(message, session)
    if user:
        stats["balance"] = user.balance
        stats["level"] = user.level.value
    lines = ["🏆 <b>ДОСТИЖЕНИЯ</b>\n"]
    for ach_id, ach_data in ACHIEVEMENTS.items():
        stat_name = ach_data["stat"]
        threshold = ach_data["threshold"]
        current = stats.get(stat_name, 0)
        if ach_id in unlocked:
            lines.append(f"✅ {ach_data['name']} — {ach_data['description']}")
        else:
            lines.append(f"🔒 {ach_data['name']} — {ach_data['description']} ({min(current, threshold)}/{threshold})")
    await message.reply("\n".join(lines), parse_mode="HTML")


@router.message(Command("license"))
@router.message(Command("права"))
async def cmd_license_group(message: types.Message, session: AsyncSession):
    import random
    user = await get_user(message, session)
    if user is None:
        return
    if user.level.value < 5:
        await message.reply("❌ Права категории «М» доступны с 5 уровня.")
        return
    already_has = await cache.get(f"user:{user.id}:license_m")
    if already_has:
        await message.reply("✅ У вас уже есть права категории «М».")
        return
    cost = 2500
    if user.balance < cost:
        await message.reply(f"❌ Недостаточно средств! Нужно {cost} ₽")
        return
    questions = [
        {"q": "Можно ли ездить на красный свет?", "a": "нет"},
        {"q": "Нужен ли шлем на электроскутере?", "a": "да"},
        {"q": "Можно ли возить пассажиров на багажнике?", "a": "нет"},
        {"q": "Разрешён ли тюнинг до 5000W с правами М?", "a": "да"},
        {"q": "Нужно ли уступать пешеходам на переходе?", "a": "да"},
    ]
    question = random.choice(questions)
    await cache.set(f"user:{user.id}:license_test", {"question": question, "attempts": 1}, expire_seconds=300)
    await message.reply(
        f"📝 <b>ТЕСТ НА ПРАВА «М»</b>\n\nВопрос: {question['q']}\n\nОтветьте «да» или «нет».\nСтоимость: {cost} ₽"
    )


@router.message(Command("transfer"))
@router.message(Command("передать"))
async def cmd_transfer_group(message: types.Message, command: CommandObject, session: AsyncSession):
    from sqlalchemy import select
    from database.models import InventoryItem
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.reply("❌ /transfer @игрок [предмет]")
        return
    recipient_str = args[0]
    item_name = " ".join(args[1:])
    if not recipient_str.startswith("@"):
        await message.reply("❌ Укажите получателя через @")
        return
    result = await session.execute(select(InventoryItem).where(InventoryItem.user_id == message.from_user.id, InventoryItem.item_name == item_name))
    item = result.scalar_one_or_none()
    if item is None:
        await message.reply(f"❌ У вас нет «{item_name}»")
        return
    if item.quantity > 1:
        item.quantity -= 1
    else:
        await session.delete(item)
    await session.commit()
    await message.reply(f"📦 <b>ПЕРЕДАЧА</b>\n\n«{item_name}» → {recipient_str}\n{recipient_str}: /accept @{message.from_user.username} {item_name}", parse_mode="HTML")


@router.message(Command("accept"))
@router.message(Command("принять"))
async def cmd_accept_group(message: types.Message, command: CommandObject, session: AsyncSession):
    from sqlalchemy import select
    from database.models import InventoryItem
    args = command.args.split() if command.args else []
    if len(args) < 2:
        await message.reply("❌ /accept @отправитель [предмет]")
        return
    item_name = " ".join(args[1:])
    result = await session.execute(select(InventoryItem).where(InventoryItem.user_id == message.from_user.id, InventoryItem.item_name == item_name))
    existing = result.scalar_one_or_none()
    if existing:
        existing.quantity += 1
    else:
        session.add(InventoryItem(user_id=message.from_user.id, item_name=item_name, quantity=1))
    await session.commit()
    await message.reply(f"✅ «{item_name}» получен!")


@router.message(Command("patrol"))
@router.message(Command("патруль"))
async def cmd_patrol_group(message: types.Message, command: CommandObject, session: AsyncSession):
    from generators.patrol_zones import generate_patrol_statuses, format_patrol_statuses
    args = command.args.split() if command.args else []
    if not args:
        statuses = await cache.get("patrol_statuses") or generate_patrol_statuses()
        await cache.set("patrol_statuses", statuses, expire_seconds=3600)
        await message.reply(format_patrol_statuses(statuses), parse_mode="HTML")
        return
    if len(args) < 2:
        await message.reply("❌ /patrol [район] [статус]\nСтатусы: тихо, обычно, рейд, облава")
        return
    zone = args[0].capitalize()
    status = args[1].lower()
    if status not in ["тихо", "обычно", "рейд", "облава"]:
        await message.reply("❌ Статусы: тихо, обычно, рейд, облава")
        return
    user = await get_user(message, session)
    display_name = f"@{user.username}" if user and user.username else message.from_user.full_name
    statuses = await cache.get("patrol_statuses") or generate_patrol_statuses()
    statuses[zone] = status
    await cache.set("patrol_statuses", statuses, expire_seconds=3600)
    from bot.handlers.chat_integration import chat_integration
    if chat_integration:
        await chat_integration.announce_patrol_info(display_name, zone, status)
    await message.reply(f"✅ Информация о патруле в {zone} обновлена! +50 XP")


@router.message(Command("faq"))
@router.message(Command("help"))
@router.message(Command("помощь"))
async def cmd_faq_group(message: types.Message):
    await message.reply(
        "❓ <b>СПРАВКА</b>\n\n"
        "/orders — взять заказ\n/garage — гараж\n/map — зоны\n/stats — профиль\n"
        "/rating — топ\n/skills — навыки\n/achievements — достижения\n"
        "/upgrade [навык] — улучшить\n/license — права\n"
        "/transfer @игрок [предмет] — передать\n/accept @игрок [предмет] — принять\n"
        "/patrol — патрули\n/faq — справка",
        parse_mode="HTML",
    )


@router.message()
async def on_mention(message: types.Message, session: AsyncSession):
    if not is_group(message.chat.type):
        return
    if not message.text:
        return
    bot_username = (await message.bot.get_me()).username
    if f"@{bot_username}" not in message.text:
        return
    text = message.text.replace(f"@{bot_username}", "").strip().lower()
    if not text or "привет" in text:
        await message.reply(f"🚴 Привет, {message.from_user.full_name}!\n\nКоманды: /orders /garage /map /stats /rating /skills /faq")
    elif "спасибо" in text:
        await message.reply("🤝 Всегда пожалуйста! Чаевые приветствуются 😄")
    else:
        await message.reply("🚴 Команды: /orders /garage /map /stats /rating /skills /faq")