from datetime import datetime

from sqlalchemy import DateTime, Integer, BigInteger, String, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chat"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    chat_type: Mapped[str] = mapped_column(String)


class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    group_id: Mapped[int] = mapped_column(Integer,  unique=True)
    name: Mapped[str] = mapped_column(String)
    screen_name: Mapped[str] = mapped_column(String)
    last_post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Binding(Base):
    __tablename__ = "bindings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    group_id: Mapped[int] = mapped_column(Integer, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    last_post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    __table_args__ = (UniqueConstraint("group_id", "chat_id"),)


class ChatAdmins(Base):
    __tablename__ = "chat_admins"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    is_creator: Mapped[bool] = mapped_column(Boolean, default=False)
