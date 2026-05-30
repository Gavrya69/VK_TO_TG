from sqlalchemy.ext.asyncio import AsyncSession

from database.db import check_subscription, add_subscription, delete_subscription


async def add_vk_group(
    session: AsyncSession,
    link: str, 
    user_id: int
):
    group_id = get_group_id(link)
    if True: # ТУТ БУДЕТ УСЛОВИЕ НА ДОСТУП К ГРУППЕ, ПОКА ЧТО TRUE
        subscribed = await check_subscription(
            session=session,
            group_id=group_id,
            user_id=user_id
        )
        if not subscribed:
            await add_subscription(
                session=session,
                group_id=group_id,
                user_id=user_id
            )
            
            return "ok"
        
        return "subscribed"
    
    return "closed"


async def delete_vk_group(
    session: AsyncSession,
    group_id: str, 
    user_id: int
):
    subscribed = await check_subscription(
        session=session,
        group_id=group_id,
        user_id=user_id
    )
    
    if subscribed:
        delete_subscription(
            session=session,
            group_id=group_id,
            user_id=user_id
        )
        return "ok"

    return "not_subscribed"


def get_group_id(link: str) -> int:
    group_id = int(link)
    return group_id

