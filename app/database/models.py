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
    
    
class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    vk_group_id: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(String(255))
    last_post_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = mapped_column(
        Integer,
        primary_key=True
    )

    user_id = mapped_column(Integer)
    group_id = mapped_column(Integer)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)

    vk_post_id: Mapped[int] = mapped_column(Integer, unique=True)
    group_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )