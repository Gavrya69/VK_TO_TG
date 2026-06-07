from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.vk import vk
from database.db import add_chat_admin, delete_chat_admins


async def sync_chat_admins(
    bot: Bot,
    session: AsyncSession,
    chat_id: int,
):
    admins = await bot.get_chat_administrators(chat_id)

    await delete_chat_admins(session, chat_id)

    for admin in admins:
        if admin.user.is_bot:
            continue
        await add_chat_admin(
            session=session,
            chat_id=chat_id,
            user_id=admin.user.id,
            is_creator=(admin.status == "creator")
        )

# TODO: ДОДЕЛАТЬ ЭТУ ФУНКЦИЮ
def add_post_info(chunk: str, c_num: int, c_count: int, author_id: int):
    chunk = f"{c_num}/{c_count}\n{chunk}" # chunk numerating
    
    return chunk