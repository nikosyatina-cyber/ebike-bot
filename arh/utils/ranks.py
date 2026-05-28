RANKS = {
    0: "🔋 Севший Аккум",
    50: "🛴 Самокатчик",
    100: "⚡ Контроллерщик",
    250: "🔧 Гаражный Механик",
    500: "🔋 Сборщик АКБ",
    1000: "⚡ Лорд Амперов",
    2500: "🚀 Убийца Контроллеров",
    5000: "👑 ElectroHub Legend"
}


def get_rank(xp: int) -> str:
    rank = "🔄 Новичок"
    for need_xp, name in sorted(RANKS.items()):
        if xp >= need_xp:
            rank = name
    return rank


def get_progress(xp: int):
    current_xp = 0
    next_xp = 50

    for need_xp in sorted(RANKS.keys()):
        if xp >= need_xp:
            current_xp = need_xp
        else:
            next_xp = need_xp
            break

    progress = xp - current_xp
    needed = next_xp - current_xp
    percent = int((progress / needed) * 100) if needed > 0 else 100

    return percent, progress, needed