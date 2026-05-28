from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, String, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserLevel(enum.IntEnum):
    STAGER = 1
    BEGINNER = 2
    RACER = 3
    EXPERIENCED = 4
    ELITE = 5
    LEGEND = 6


class TransportType(enum.Enum):
    MECHANIC = "mechanic"
    YANDEX_SCOOTER = "yandex_scooter"
    YANDEX_BIKE = "yandex_bike"
    WENBOX_RENT = "wenbox_rent"
    U2U7_RENT = "u2u7_rent"
    WENBOX_OWN = "wenbox_own"
    U2U7_OWN = "u2u7_own"


class Platform(enum.Enum):
    YANDEX = "yandex"
    DOSTAVISTA = "dostavista"
    X5 = "x5"
    MAGNIT = "magnit"
    OZON = "ozon"
    WB = "wb"
    TOPGO = "topgo"
    VKUSVILL = "vkusvill"
    BLACK_MARKET = "black_market"
    ELITE = "elite"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128), default="Курьер")
    level: Mapped[UserLevel] = mapped_column(Enum(UserLevel), default=UserLevel.STAGER)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[float] = mapped_column(Float, default=500.0)
    current_transport: Mapped[TransportType] = mapped_column(Enum(TransportType), default=TransportType.MECHANIC)
    current_platform: Mapped[Optional[Platform]] = mapped_column(Enum(Platform), nullable=True)
    battery_charge: Mapped[int] = mapped_column(Integer, default=100)
    reputation: Mapped[int] = mapped_column(Integer, default=50)
    social_rating: Mapped[int] = mapped_column(Integer, default=0)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    transport: Mapped[Optional["UserTransport"]] = relationship("UserTransport", back_populates="user", uselist=False)
    inventory: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, level={self.level})>"


class UserTransport(Base):
    __tablename__ = "user_transport"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    transport_type: Mapped[TransportType] = mapped_column(Enum(TransportType))
    chain_wear: Mapped[float] = mapped_column(Float, default=0.0)
    brake_wear: Mapped[float] = mapped_column(Float, default=0.0)
    battery_wear: Mapped[float] = mapped_column(Float, default=0.0)
    motor_power: Mapped[int] = mapped_column(Integer, default=500)
    controller_amps: Mapped[int] = mapped_column(Integer, default=30)
    battery_voltage: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    total_km: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship("User", back_populates="transport")


class InventoryItem(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    item_name: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship("User", back_populates="inventory")


class OrderHistory(Base):
    __tablename__ = "order_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    platform: Mapped[Platform] = mapped_column(Enum(Platform))
    food: Mapped[str] = mapped_column(String(128))
    distance_km: Mapped[float] = mapped_column(Float)
    pay: Mapped[float] = mapped_column(Float)
    tips: Mapped[float] = mapped_column(Float, default=0.0)
    was_on_time: Mapped[bool] = mapped_column(Boolean, default=True)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())