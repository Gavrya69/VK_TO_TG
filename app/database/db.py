from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base, Group, Chat, Binding, ChatAdmins

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
    name: str,
    screen_name: str,
    last_post_id: int,
):
    group = Group(
        vk_group_id=vk_group_id,
        name=name,
        screen_name=screen_name,
        last_post_id=last_post_id,
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


async def get_groups(
    session: AsyncSession
):
    result = await session.execute(
        select(Group)
    )
    
    return result.scalars().all()


async def update_group_last_post_id(
    session: AsyncSession,
    group_id: int,
    last_post_id: int
):
    group = await session.get(Group, group_id)
    
    if group:
        group.last_post_id = last_post_id
        await session.commit()

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

async def get_chats(
    session: AsyncSession,
    chat_ids: list[int]
):
    if not chat_ids:
        return []

    result = await session.execute(
        select(Chat).where(Chat.telegram_chat_id.in_(chat_ids))
    )

    return result.scalars().all()

# --------------------
# BINDINGS (VK -> TG)
# --------------------

async def add_binding(
    session: AsyncSession,
    vk_group_id: int,
    telegram_chat_id: int,
    last_post_id: int,
):
    binding = Binding(
        vk_group_id=vk_group_id,
        telegram_chat_id=telegram_chat_id,
        last_post_id=last_post_id,
    )

    session.add(binding)
    await session.commit()
    
    return binding


async def get_binding(
    session: AsyncSession, 
    vk_group_id: int,
    telegram_chat_id: int
):
    result = await session.execute(
        select(Binding).where(
            Binding.vk_group_id == vk_group_id, 
            Binding.telegram_chat_id == telegram_chat_id)
    )
    
    return result.scalar_one_or_none()


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


async def get_bindings_with_groups(
    session: AsyncSession,
    telegram_chat_id: int
):
    result = await session.execute(
        select(Binding, Group)
        .join(Group, Binding.vk_group_id == Group.vk_group_id)
        .where(Binding.telegram_chat_id == telegram_chat_id)
    )

    return result.all()


async def update_binding_last_post_id(
    session: AsyncSession,
    vk_group_id: int,
    telegram_chat_id: int,
    last_post_id: int,
):
    result = await session.execute(
        select(Binding).where(
            Binding.vk_group_id == vk_group_id,
            Binding.telegram_chat_id == telegram_chat_id,
        )
    )
    
    binding = result.scalar_one_or_none()
    
    if binding:
        binding.last_post_id = last_post_id
        await session.commit()
        
        
async def get_pending_bindings(
    session: AsyncSession,
    vk_group_id: int,
    post_id: int,
):
    result = await session.execute(
        select(Binding).where(
            Binding.vk_group_id == vk_group_id,
            (
                (Binding.last_post_id.is_(None)) | (Binding.last_post_id < post_id)
            )
        )
    )
    
    return result.scalars().all()


async def get_min_last_post_id(
    session,
    vk_group_id: int,
) -> int | None:
    result = await session.execute(
        select(func.min(Binding.last_post_id))
        .where(Binding.vk_group_id == vk_group_id)
    )

    return result.scalar_one_or_none()

# --------------------
# CHAT ADMINS
# --------------------

async def add_chat_admin(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
    is_creator: bool
):
    admin = ChatAdmins(
        chat_id=chat_id,
        user_id=user_id,
        is_creator=is_creator,
    )

    session.add(admin)
    await session.commit()
    
    return admin


async def get_chats_by_admin(
    session: AsyncSession,
    user_id: int,
):
    result = await session.execute(
        select(ChatAdmins).where(ChatAdmins.user_id == user_id)
    )
    
    return result.scalars().all()   # without commit


async def delete_chat_admins(
    session: AsyncSession,
    chat_id: int,
):
    await session.execute(
        delete(ChatAdmins).where(
            ChatAdmins.chat_id == chat_id
        )
    )
    await session.commit()


async def is_chat_admin(
    session: AsyncSession,
    chat_id: int,
    user_id: int,
) -> bool:

    result = await session.execute(
        select(ChatAdmins).where(
            ChatAdmins.chat_id == chat_id,
            ChatAdmins.user_id == user_id,
    ))

    return result.scalar_one_or_none() is not None

# --------------------
# OTHER
# --------------------

async def clear_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)