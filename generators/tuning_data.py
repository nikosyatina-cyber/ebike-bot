MOTORS = {
    "motor_stock": {"name": "Стоковый 500W", "power": 500, "price": 0, "max_speed": 35, "requirements": {}, "description": "Надёжный базовый мотор."},
    "motor_city": {"name": "Городской 1000W", "power": 1000, "price": 5000, "max_speed": 45, "requirements": {"controller_amps": 50}},
    "motor_dynamic": {"name": "Динамичный 1500W", "power": 1500, "price": 9000, "max_speed": 55, "requirements": {"controller_amps": 80, "pendulum": "reinforced"}},
    "motor_sport": {"name": "Спортивный 2000W", "power": 2000, "price": 15000, "max_speed": 65, "requirements": {"controller_amps": 120, "pendulum": "racing"}},
    "motor_turbo": {"name": "Турбо 3000W", "power": 3000, "price": 25000, "max_speed": 75, "requirements": {"controller_amps": 180, "pendulum": "racing", "battery_voltage": "72V"}},
    "motor_beast": {"name": "Зверь 4000W", "power": 4000, "price": 40000, "max_speed": 85, "requirements": {"controller_amps": 250, "pendulum": "carbon", "battery_voltage": "72V", "battery_min_ah": 40}},
    "motor_absolute": {"name": "Абсолют 5000W", "power": 5000, "price": 70000, "max_speed": 100, "requirements": {"controller_amps": 300, "pendulum": "carbon", "battery_voltage": "72V", "battery_min_ah": 80, "frame": "reinforced"}},
}

CONTROLLERS = {
    "controller_stock": {"name": "Стоковый 30А", "amps": 30, "price": 0, "speed_bonus": 0, "consumption_mult": 1.0},
    "controller_50a": {"name": "Уверенный 50А", "amps": 50, "price": 4000, "speed_bonus": 10, "consumption_mult": 1.2},
    "controller_80a": {"name": "Быстрый 80А", "amps": 80, "price": 8000, "speed_bonus": 15, "consumption_mult": 1.4},
    "controller_120a": {"name": "Мощный 120А", "amps": 120, "price": 14000, "speed_bonus": 20, "consumption_mult": 1.7},
    "controller_180a": {"name": "Злой 180А", "amps": 180, "price": 22000, "speed_bonus": 25, "consumption_mult": 2.0},
    "controller_250a": {"name": "Бешеный 250А", "amps": 250, "price": 35000, "speed_bonus": 30, "consumption_mult": 2.8},
    "controller_300a": {"name": "Экстрим 300А", "amps": 300, "price": 55000, "speed_bonus": 35, "consumption_mult": 3.5},
}

BATTERIES = {
    "battery_60v40": {"name": "Базовая 60V 40Ah", "voltage": "60V", "capacity_ah": 40, "price": 0, "range_km": 60, "weight_penalty": 0},
    "battery_60v60": {"name": "Усиленная 60V 60Ah", "voltage": "60V", "capacity_ah": 60, "price": 8000, "range_km": 90, "weight_penalty": 5},
    "battery_72v40": {"name": "Высоковольтная 72V 40Ah", "voltage": "72V", "capacity_ah": 40, "price": 15000, "range_km": 55, "weight_penalty": 0},
    "battery_72v60": {"name": "Мощная 72V 60Ah", "voltage": "72V", "capacity_ah": 60, "price": 25000, "range_km": 80, "weight_penalty": 7},
    "battery_72v80": {"name": "Максимальная 72V 80Ah", "voltage": "72V", "capacity_ah": 80, "price": 45000, "range_km": 110, "weight_penalty": 10},
}

PENDULUMS = {
    "pendulum_stock": {"name": "Стоковый", "price": 0, "durability": 50},
    "pendulum_reinforced": {"name": "Усиленный", "price": 2500, "durability": 70},
    "pendulum_racing": {"name": "Гоночный", "price": 6000, "durability": 85},
    "pendulum_carbon": {"name": "Карбоновый", "price": 15000, "durability": 95},
}

BRAKE_SYSTEMS = {
    "brake_mech": {"name": "Механика", "price": 0, "efficiency": 40},
    "brake_hydro": {"name": "Гидравлика", "price": 3000, "efficiency": 65},
    "brake_sport": {"name": "Спорт-гидравлика", "price": 7000, "efficiency": 85},
    "brake_radial": {"name": "Радиал 4 поршня", "price": 12000, "efficiency": 95},
}

VISUALS = {
    "paint_black": {"name": "⚫ Матовый чёрный", "price": 800, "type": "paint", "bonus": "Чёрный рынок +5%"},
    "paint_red": {"name": "🔴 Красный", "price": 1000, "type": "paint", "bonus": "Скорость +3%"},
    "paint_chrome": {"name": "💎 Хром", "price": 3500, "type": "paint", "bonus": "Элитные +15%"},
    "vinyl_flame": {"name": "🔥 Огонь", "price": 1500, "type": "vinyl", "bonus": "Чаевые +10%"},
    "vinyl_snake": {"name": "🐍 Змея", "price": 2000, "type": "vinyl", "bonus": "ЧР +10%"},
    "vinyl_racing": {"name": "🏁 Гоночные", "price": 2500, "type": "vinyl", "bonus": "Стиль"},
}