from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base, Group, Post, Subscription

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


async def add_group(
    session: AsyncSession,
    vk_group_id: int,
    title: str,
):
    group = Group(
        vk_group_id=vk_group_id,
        title=title,
    )

    session.add(group)
    await session.commit()

    return group


async def get_group(
    session: AsyncSession,
    vk_group_id: int,
):
    query = select(Group).where(
        Group.vk_group_id == vk_group_id
    )

    result = await session.execute(query)

    return result.scalar_one_or_none()


async def add_post(
    session: AsyncSession,
    vk_post_id: int,
    group_id: int,
):
    post = Post(
        vk_post_id=vk_post_id,
        group_id=group_id,
    )

    session.add(post)
    await session.commit()

    return post


async def add_subscription(
    session: AsyncSession,
    user_id: int,
    group_id: int,
):
    subscription = Subscription(
        user_id=user_id,
        group_id=group_id,
    )

    session.add(subscription)
    await session.commit()

    return subscription


async def check_subscription(
    session: AsyncSession,
    group_id: int,
    user_id: int
):    
    query = select(Subscription).where(
        Subscription.group_id == group_id,
        Subscription.user_id == user_id
    )

    result = await session.execute(query)
    
    return result.scalar_one_or_none()


async def get_subscriptions(
    session: AsyncSession,
    user_id: int
):
    query = select(Subscription).where(
        Subscription.user_id == user_id
    )
    
    result = await session.execute(query)

    return result.scalars().all()


async def delete_subscription(
    session: AsyncSession,
    user_id: int,
    group_id: int,
):
    await session.execute(
        delete(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.group_id == group_id,
        )
    )

    await session.commit()


async def clear_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
