import random
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class Order:
    id: str
    platform: str
    restaurant: str
    food: str
    restaurant_distance: float
    client_distance: float
    total_distance: float
    base_pay: int
    weight: str
    urgency: str
    time_limit: int
    zone: str = "Центр"

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

    def format_message(self) -> str:
        ue = {"обычный": "🟢", "срочный": "🟡", "премиум": "🔴"}
        we = {"лёгкий": "🪶", "средний": "📦", "тяжёлый": "🏋️", "очень тяжёлый": "💪"}
        return (
            f"{ue.get(self.urgency, '🟢')} <b>{self.food}</b>\n"
            f"├── Ресторан: {self.restaurant}\n"
            f"├── Расстояние: {self.total_distance} км\n"
            f"├── Вес: {we.get(self.weight, '📦')} {self.weight}\n"
            f"├── Оплата: <b>{self.base_pay} ₽</b>\n"
            f"└── Таймер: {self.time_limit} мин\n"
        )


class OrderGenerator:
    PLATFORM_CONFIG = {
        "yandex": {
            "restaurants": ["Пиццерия «Тесто»", "Суши-бар «Рис»", "Бургерная «Мясо»", "WOK «Лапша»", "Кофейня «Зерно»"],
            "food_types": ["Пицца Маргарита", "Суши Филадельфия", "Бургер Блэк", "Лапша WOK", "Латте", "Круассан"],
            "base_pay_range": (100, 300),
            "distance_range": (0.5, 8.0),
            "weight_options": ["лёгкий", "средний"],
            "time_per_km": 4,
        },
        "dostavista": {
            "restaurants": ["Частный заказчик"],
            "food_types": ["Документы", "Цветы", "Подарок", "Ключи", "Лекарства"],
            "base_pay_range": (50, 500),
            "distance_range": (1.0, 15.0),
            "weight_options": ["лёгкий"],
            "time_per_km": 3,
        },
        "x5": {
            "restaurants": ["Пятёрочка", "Перекрёсток", "Карусель"],
            "food_types": ["Продукты набор", "Бакалея", "Молочка", "Хлеб", "Овощи"],
            "base_pay_range": (200, 500),
            "distance_range": (1.0, 8.0),
            "weight_options": ["средний", "тяжёлый"],
            "time_per_km": 5,
        },
        "magnit": {
            "restaurants": ["Магнит", "Магнит Косметик"],
            "food_types": ["Бакалея", "Вода 5л", "Масло растительное", "Консервы набор", "Бытовая химия"],
            "base_pay_range": (250, 550),
            "distance_range": (0.5, 3.0),
            "weight_options": ["средний", "тяжёлый", "очень тяжёлый"],
            "time_per_km": 6,
        },
        "ozon": {
            "restaurants": ["Озон Склад"],
            "food_types": ["Молочка фермерская", "Рыба охлаждённая", "Мясо мраморное", "Овощи органик"],
            "base_pay_range": (300, 700),
            "distance_range": (0.5, 3.0),
            "weight_options": ["средний", "тяжёлый"],
            "time_per_km": 4,
        },
        "wb": {
            "restaurants": ["ПВЗ Wildberries"],
            "food_types": ["Посылка", "Одежда", "Электроника", "Товары для дома"],
            "base_pay_range": (80, 200),
            "distance_range": (0.3, 2.0),
            "weight_options": ["лёгкий", "средний", "тяжёлый"],
            "time_per_km": 7,
        },
        "topgo": {
            "restaurants": ["TopGO Склад"],
            "food_types": ["Смартфон", "Аксессуары", "Гаджеты", "Наушники"],
            "base_pay_range": (150, 400),
            "distance_range": (0.5, 3.0),
            "weight_options": ["лёгкий", "средний"],
            "time_per_km": 4,
        },
        "vkusvill": {
            "restaurants": ["ВкусВилл"],
            "food_types": ["Молочка", "Сыры", "Колбасы", "Хлеб", "Сметана"],
            "base_pay_range": (80, 150),
            "distance_range": (0.3, 3.0),
            "weight_options": ["лёгкий", "средний"],
            "time_per_km": 5,
        },
        "black_market": {
            "restaurants": ["Аноним"],
            "food_types": ["Груз серый", "Аптечка", "Сим-карты", "Флешка"],
            "base_pay_range": (800, 5000),
            "distance_range": (1.0, 8.0),
            "weight_options": ["лёгкий", "средний"],
            "time_per_km": 4,
        },
        "elite": {
            "restaurants": ["Ресторан Michelin", "Частный повар", "Бутик", "Ювелирный"],
            "food_types": ["Ужин от шефа", "Десерт эксклюзив", "Подарок VIP", "Кольцо"],
            "base_pay_range": (1000, 4000),
            "distance_range": (1.0, 10.0),
            "weight_options": ["лёгкий", "средний"],
            "time_per_km": 4,
        },
    }

    ZONES = ["Центр", "Северный", "Южный", "Восточный", "Западный", "Пригород"]

    def generate_orders(
        self,
        platform: str,
        count: int = 5,
        weather_multiplier: float = 1.0,
        event_multiplier: float = 1.0,
    ) -> List[Order]:
        """Генерирует список заказов для платформы."""
        config = self.PLATFORM_CONFIG.get(platform)
        if config is None:
            return []

        orders = []
        for _ in range(count):
            order = self._generate_single(
                platform=platform,
                config=config,
                weather_multiplier=weather_multiplier,
                event_multiplier=event_multiplier,
            )
            orders.append(order)

        return orders

    def _generate_single(
        self,
        platform: str,
        config: dict,
        weather_multiplier: float,
        event_multiplier: float,
    ) -> Order:
        """Генерирует один заказ."""
        restaurant = random.choice(config["restaurants"])
        food = random.choice(config["food_types"])
        weight = random.choice(config["weight_options"])
        zone = random.choice(self.ZONES)

        rest_dist = round(random.uniform(*config["distance_range"]), 1)
        client_dist = round(random.uniform(*config["distance_range"]), 1)
        total_dist = round(rest_dist + client_dist, 1)

        base_pay = random.randint(*config["base_pay_range"])
        pay = int(base_pay * weather_multiplier * event_multiplier)

        time_per_km = config["time_per_km"]
        time_limit = max(5, int(total_dist * time_per_km))

        urgency_roll = random.random()
        if urgency_roll < 0.1:
            urgency = "премиум"
            pay = int(pay * 1.5)
            time_limit = max(3, int(time_limit * 0.7))
        elif urgency_roll < 0.3:
            urgency = "срочный"
            pay = int(pay * 1.2)
            time_limit = max(4, int(time_limit * 0.85))
        else:
            urgency = "обычный"

        if platform == "wb":
            time_limit = 999

        if platform == "ozon":
            time_limit = max(3, int(time_limit * 0.8))

        order_id = f"{platform}_{random.randint(10000, 99999)}"

        return Order(
            id=order_id,
            platform=platform,
            restaurant=restaurant,
            food=food,
            restaurant_distance=rest_dist,
            client_distance=client_dist,
            total_distance=total_dist,
            base_pay=pay,
            weight=weight,
            urgency=urgency,
            time_limit=time_limit,
            zone=zone,
        )