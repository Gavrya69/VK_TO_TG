from datetime import datetime

from sqlalchemy import DateTime, Integer, BigInteger, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(Integer, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(Integer)
    group_id: Mapped[int] = mapped_column(Integer)
    tg_chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    tg_thread_id: Mapped[int] = mapped_column(Integer, nullable=True)


class TelegramTarget(Base):
    __tablename__ = "telegram_targets"

    id: Mapped[int] = mapped_column(primary_key=True)

    owner_id: Mapped[int]
    chat_id: Mapped[int]
    title: Mapped[str]
    chat_type: Mapped[str]