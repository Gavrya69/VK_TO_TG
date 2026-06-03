from datetime import datetime

from sqlalchemy import DateTime, Integer, BigInteger, String, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

    
class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    vk_group_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    screen_name: Mapped[str] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    last_post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    
class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    chat_type: Mapped[str] = mapped_column(String)


class Binding(Base):
    __tablename__ = "bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    vk_group_id: Mapped[int] = mapped_column(Integer, index=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    telegram_thread_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("vk_group_id", "telegram_chat_id", "telegram_thread_id"),
    )


class ChatAdmins(Base):
    __tablename__ = "chat_admins"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
