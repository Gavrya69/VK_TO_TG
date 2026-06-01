from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base, Group, Chat, Binding

DATABASE_URL = "sqlite+aiosqlite:///data/database.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --------------------
# VK GROUPS
# --------------------

async def add_group(
    session: AsyncSession, 
    vk_group_id: int, 
    name: str
):
    group = Group(
        vk_group_id=vk_group_id,
        name=name,
    )

    session.add(group)
    await session.commit()
    
    return group


async def get_group(
    session: AsyncSession, 
    vk_group_id: int
):
    result = await session.execute(
        select(Group).where(Group.vk_group_id == vk_group_id)
    )
    
    return result.scalar_one_or_none()


# --------------------
# TG CHATS
# --------------------

async def add_chat(
    session: AsyncSession,
    chat_id: int,
    title: str,
    chat_type: str,
):
    chat = Chat(
        telegram_chat_id=chat_id,
        title=title,
        chat_type=chat_type,
    )

    session.add(chat)
    await session.commit()
    
    return chat


async def get_chat(
    session: AsyncSession, 
    chat_id: int
):
    result = await session.execute(
        select(Chat).where(Chat.telegram_chat_id == chat_id)
    )
    
    return result.scalar_one_or_none()


# --------------------
# BINDINGS (VK -> TG)
# --------------------

async def add_binding(
    session: AsyncSession,
    vk_group_id: int,
    telegram_chat_id: int,
    telegram_thread_id: int | None = None,
):
    binding = Binding(
        vk_group_id=vk_group_id,
        telegram_chat_id=telegram_chat_id,
        telegram_thread_id=telegram_thread_id,
    )

    session.add(binding)
    await session.commit()
    
    return binding


async def get_bindings_by_group(
    session: AsyncSession,
    vk_group_id: int,
):
    result = await session.execute(
        select(Binding).where(Binding.vk_group_id == vk_group_id)
    )
    
    return result.scalars().all()


async def get_bindings_by_chat(
    session: AsyncSession,
    telegram_chat_id: int,
):
    result = await session.execute(
        select(Binding).where(Binding.telegram_chat_id == telegram_chat_id)
    )
    
    return result.scalars().all()


async def delete_binding(
    session: AsyncSession,
    vk_group_id: int,
    telegram_chat_id: int,
):
    await session.execute(
        delete(Binding).where(
            Binding.vk_group_id == vk_group_id,
            Binding.telegram_chat_id == telegram_chat_id,
        )
    )
    await session.commit()


async def clear_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)