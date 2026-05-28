import random

from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud import UserCRUD
from database.models import UserLevel
from database.engine import cache
from generators.zones import ZONES


router = Router()


def calc_power(user) -> int:
    """Рассчитывает силу бойца."""
    tb = {
        "mechanic": 0,
        "yandex_scooter": -2,
        "yandex_bike": 1,
        "wenbox_rent": 2,
        "u2u7_rent": 4,
        "wenbox_own": 3,
        "u2u7_own": 5,
    }
    t = user.current_transport.value if hasattr(user.current_transport, 'value') else str(user.current_transport)
    return max(0, tb.get(t, 0) + user.level.value * 2 + user.reputation // 20)


def get_display_name(user) -> str:
    """Возвращает отображаемое имя игрока."""
    if user.username:
        return f"@{user.username}"
    return user.full_name or f"ID:{user.id}"


@router.message(F.text == "🌍 Карта")
async def cmd_map(message: types.Message, session: AsyncSession) -> None:
    """Показывает карту зон."""
    user_crud = UserCRUD(session)
    user = await user_crud.get(message.from_user.id)

    if user is None:
        return

    zc = await cache.hgetall("zones:control") or {}

    txt = "🌍 <b>ЗОНЫ ГОРОДА</b>\n\n"

    for zone_key, zone_data in ZONES.items():
        owner_id = zc.get(zone_key)

        if owner_id:
            try:
                owner = await user_crud.get(int(owner_id))
                owner_name = get_display_name(owner) if owner else f"ID:{owner_id}"
            except (ValueError, TypeError):
                owner_name = str(owner_id)
        else:
            owner_name = "Свободна"

        txt += (
            f"{zone_data['name']}\n"
            f"├── Владелец: {owner_name}\n"
            f"├── Бонус: {zone_data['bonus_description']}\n"
            f"└── /захват_{zone_key}\n\n"
        )

    await message.answer(txt, parse_mode="HTML")


@router.message(F.text.startswith("/захват_"))
async def cmd_capture(message: types.Message, session: AsyncSession) -> None:
    """Попытка захвата зоны."""
    uid = message.from_user.id
    uc = UserCRUD(session)
    user = await uc.get(uid)

    if user is None:
        return

    if user.level < UserLevel.BEGINNER:
        await message.answer("❌ Захват зон доступен со 2 уровня (Подаван).")
        return

    zk = message.text.replace("/захват_", "").strip()
    zd = ZONES.get(zk)

    if zd is None:
        zones_list = "\n".join([f"/захват_{k} — {v['name']}" for k, v in ZONES.items()])
        await message.answer(f"❌ Неизвестная зона. Доступные:\n{zones_list}")
        return

    zc = await cache.hgetall("zones:control") or {}
    co = zc.get(zk)

    # Проверяем, не владеет ли уже игрок этой зоной
    if co and str(co) == str(uid):
        await message.answer(f"❌ Вы уже контролируете {zd['name']}.")
        return

    # Если зона свободна — захватываем
    if co is None:
        await cache.hset("zones:control", zk, str(uid))
        await cache.hset("zones:names", zk, get_display_name(user))
        await message.answer(
            f"✅ <b>ЗОНА ЗАХВАЧЕНА!</b>\n\n"
            f"{zd['name']} теперь под вашим контролем!\n"
            f"Бонус: {zd['bonus_description']}",
            parse_mode="HTML",
        )
        return

    # Зона занята — драка
    did = int(co)
    defender = await uc.get(did)

    if defender is None:
        await cache.hset("zones:control", zk, str(uid))
        await cache.hset("zones:names", zk, get_display_name(user))
        await message.answer(
            f"✅ Защитник покинул игру. {zd['name']} переходит к вам!",
            parse_mode="HTML",
        )
        return

    # Силы бойцов
    ap = calc_power(user)
    dp = calc_power(defender)

    attacker_name = get_display_name(user)
    defender_name = get_display_name(defender)

    aw, dw = 0, 0
    rounds = []

    for r in range(1, 4):
        ar, dr = random.randint(1, 20), random.randint(1, 20)
        a_total = ap + ar
        d_total = dp + dr

        if a_total > d_total:
            aw += 1
            rounds.append(f"Раунд {r}: 🟢 {attacker_name} ({a_total} vs {d_total})")
        else:
            dw += 1
            rounds.append(f"Раунд {r}: 🔴 {defender_name} ({d_total} vs {a_total})")

        if aw >= 2 or dw >= 2:
            break

    result_text = (
        f"💀 <b>ДРАКА ЗА {zd['name']}!</b>\n\n"
        f"⚔️ {attacker_name} vs {defender_name}\n\n"
        + "\n".join(rounds) + "\n\n"
    )

    if aw >= 2:
        await cache.hset("zones:control", zk, str(uid))
        await cache.hset("zones:names", zk, attacker_name)
        result_text += f"🏆 <b>ПОБЕДИТЕЛЬ: {attacker_name}!</b>\n"
        result_text += f"Зона переходит под ваш контроль!"
    else:
        result_text += f"🛡 <b>ЗАЩИТНИК УДЕРЖАЛ ЗОНУ: {defender_name}!</b>\n"
        result_text += f"Попробуйте снова через 24 часа."

    await message.answer(result_text, parse_mode="HTML")