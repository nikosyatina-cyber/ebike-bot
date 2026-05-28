import random
from datetime import datetime
from typing import Dict, Any


class WeatherGenerator:
    """Генератор погоды."""

    WEATHER_TABLE = [
        {
            "roll": (1, 1),
            "temperature": "🥶 -15°C и ниже",
            "precipitation": "❄️ Снегопад",
            "pay_multiplier": 1.5,
            "speed_penalty": 0.40,
            "battery_penalty": 0.40,
            "fall_chance": 0.25,
            "description": "Батареи садятся на 40% быстрее. Сильный гололёд.",
        },
        {
            "roll": (2, 4),
            "temperature": "🥶 -5...-10°C",
            "precipitation": "❄️ Снег",
            "pay_multiplier": 1.3,
            "speed_penalty": 0.30,
            "battery_penalty": 0.25,
            "fall_chance": 0.20,
            "description": "Гололёд, шанс падения +20%.",
        },
        {
            "roll": (5, 7),
            "temperature": "🌡️ 0...+5°C",
            "precipitation": "🌧️ Дождь со снегом",
            "pay_multiplier": 1.2,
            "speed_penalty": 0.15,
            "visibility_penalty": 0.10,
            "description": "Мокрый снег, видимость снижена.",
        },
        {
            "roll": (8, 10),
            "temperature": "🌧️ +5...+10°C",
            "precipitation": "🌧️ Дождь",
            "pay_multiplier": 1.6,
            "speed_penalty": 0.20,
            "braking_penalty": 0.15,
            "description": "Мокрый асфальт, тормозной путь +15%.",
        },
        {
            "roll": (11, 14),
            "temperature": "☁️ +10...+18°C",
            "precipitation": "☁️ Облачно",
            "pay_multiplier": 1.0,
            "speed_penalty": 0.0,
            "description": "Обычная погода, работать комфортно.",
        },
        {
            "roll": (15, 17),
            "temperature": "☀️ +18...+25°C",
            "precipitation": "☀️ Ясно",
            "pay_multiplier": 1.0,
            "speed_penalty": 0.0,
            "description": "Идеальные условия для доставки.",
        },
        {
            "roll": (18, 19),
            "temperature": "🌡️ +25...+32°C",
            "precipitation": "☀️ Жарко",
            "pay_multiplier": 1.1,
            "speed_penalty": 0.0,
            "fatigue_penalty": 0.20,
            "description": "Душно, чаще нужна вода.",
        },
        {
            "roll": (20, 20),
            "temperature": "🌡️ +32°C и выше",
            "precipitation": "☀️ Зной",
            "pay_multiplier": 1.2,
            "speed_penalty": 0.05,
            "battery_overheat": 0.10,
            "fatigue_penalty": 0.30,
            "description": "Батарея перегревается, риск отказа 10%.",
        },
    ]

    EXTRA_MODIFIERS = [
        {
            "name": "🌫️ Туман",
            "chance": 0.15,
            "effects": {"visibility_penalty": 0.30},
        },
        {
            "name": "💨 Шквальный ветер",
            "chance": 0.10,
            "effects": {"speed_penalty": 0.25, "cargo_risk": True},
        },
        {
            "name": "⛈ Гроза",
            "chance": 0.05,
            "effects": {"pay_multiplier": 2.0, "lightning_risk": 0.02},
        },
    ]

    # Время суток влияет на температуру
    HOUR_MODIFIERS = {
        # часы: (модификатор температуры, склонность к осадкам)
        (0, 5): ("ночь", -3, 0.8),  # ночью холоднее
        (6, 11): ("утро", 0, 0.6),  # утром нормально
        (12, 17): ("день", 3, 0.3),  # днём теплее, меньше осадков
        (18, 23): ("вечер", -1, 0.5),  # вечером прохладнее
    }

    def generate(self) -> Dict[str, Any]:
        """Генерирует погоду с учётом времени суток."""
        now = datetime.now()
        hour = now.hour

        # Определяем время суток
        time_of_day = "день"
        temp_modifier = 0
        precip_chance_mod = 0.5

        for (start, end), (tod, tmod, pchance) in self.HOUR_MODIFIERS.items():
            if start <= hour <= end:
                time_of_day = tod
                temp_modifier = tmod
                precip_chance_mod = pchance
                break

        roll = random.randint(1, 20)
        # Ночью и вечером сдвигаем бросок в сторону холодной погоды
        if time_of_day in ["ночь", "вечер"]:
            roll = max(1, roll - 2)
        # Днём — в сторону тёплой
        elif time_of_day == "день":
            roll = min(20, roll + 2)

        weather = {
            "temperature": "☁️ +15°C",
            "precipitation": "☁️ Облачно",
            "pay_multiplier": 1.0,
            "speed_penalty": 0.0,
            "battery_penalty": 0.0,
            "fall_chance": 0.0,
            "fatigue_penalty": 0.0,
            "visibility_penalty": 0.0,
            "braking_penalty": 0.0,
            "battery_overheat": 0.0,
            "description": "Обычный день.",
            "extra_modifiers": [],
            "time_of_day": time_of_day,
        }

        for entry in self.WEATHER_TABLE:
            if entry["roll"][0] <= roll <= entry["roll"][1]:
                for key in weather:
                    if key in entry:
                        weather[key] = entry[key]
                break

        # Дополнительные модификаторы (с учётом времени суток)
        for mod in self.EXTRA_MODIFIERS:
            actual_chance = mod["chance"] * precip_chance_mod
            if random.random() < actual_chance:
                weather["extra_modifiers"].append(mod)
                for key, value in mod["effects"].items():
                    weather[key] = weather.get(key, 0.0) + value

        return weather

    def get_platform_multiplier(self, weather: Dict[str, Any], platform: str) -> float:
        """Рассчитывает множитель оплаты для платформы."""
        base = weather.get("pay_multiplier", 1.0)

        if platform == "yandex":
            precip = weather.get("precipitation", "")
            if "Дождь" in precip:
                base = max(base, 1.8)
            elif "Снег" in precip:
                base = max(base, 1.5)
            elif any("Гроза" in mod.get("name", "") for mod in weather.get("extra_modifiers", [])):
                base = max(base, 2.0)

        return base

    def format_message(self, weather: Dict[str, Any]) -> str:
        """Форматирует часовую сводку погоды."""
        now = datetime.now()

        time_emoji = {
            "ночь": "🌙",
            "утро": "🌅",
            "день": "☀️",
            "вечер": "🌆",
        }

        tod = weather.get("time_of_day", "день")
        emoji = time_emoji.get(tod, "☀️")

        msg = f"{emoji} <b>СВОДКА НА {now.hour}:00</b>\n\n"
        msg += f"🌡️ Температура: {weather['temperature']}\n"
        msg += f"🌧️ Осадки: {weather['precipitation']}\n"

        for mod in weather.get("extra_modifiers", []):
            msg += f"{mod['name']} {mod['name']}\n"

        msg += f"\n📊 <b>ВЛИЯНИЕ НА ПЛАТФОРМЫ:</b>\n"
        msg += f"├── 🟡 Яндекс.Еда: x{self.get_platform_multiplier(weather, 'yandex')}\n"
        msg += f"├── 🔵 Озон: {'Штрафов нет' if weather.get('speed_penalty', 0) < 0.2 else 'Осторожно на дороге!'}\n"
        msg += f"└── 🏍 Патрули: {'Активны' if weather.get('speed_penalty', 0) > 0.1 else 'Обычный режим'}\n"

        # Рекомендация
        precip = weather.get("precipitation", "")
        temp = weather.get("temperature", "")

        if "Дождь" in precip:
            rec = "🧥 Возьмите дождевик!"
        elif "Снег" in precip:
            rec = "🧤 Наденьте термоперчатки!"
        elif "Жарко" in temp or "Зной" in temp:
            rec = "💧 Пейте больше воды!"
        elif "Мороз" in temp or "-" in temp:
            rec = "🧣 Одевайтесь теплее!"
        else:
            rec = "✅ Можно ехать налегке"

        msg += f"\n🎒 <b>Рекомендация:</b> {rec}"

        return msg


weather_generator = WeatherGenerator()