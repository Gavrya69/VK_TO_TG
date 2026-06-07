import time

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
def format_post(post: dict) -> str:
    parts = []
    
    struct_time = time.localtime(post["date"])
    formatted_time = time.strftime("%d.%m.%Y %H:%M:%S", struct_time) 
    parts.append(f"📅 Дата: {formatted_time}")
    
    author = post.get("author_info")
    if author:
        parts.append(f"👤 Автор: {author["first_name"]} {author["last_name"]}")
        
    parts.append(f"🔗 Ссылка: https://vk.com/wall{post['from_id']}_{post['id']}")
    
    parts.append("")
    parts.append(post["text"])
    
    return "\n".join(parts)