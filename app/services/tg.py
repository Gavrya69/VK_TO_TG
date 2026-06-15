from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.vk.client import vk
from services.vk.models import VKPost, VKUser, VKGroup
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
        await session.commit()


# TODO: (Отформатировать информацию как цитату, добавить гиперссылку на автора)
def format_post(post: VKPost) -> str:
    parts = []
    
    formatted_time = post.date.strftime("%d.%m.%Y %H:%M:%S") 
    parts.append(f"📅 Дата: {formatted_time}")
    
    if post.author and post.author.id != abs(post.owner_id):
        if isinstance(post.author, VKUser):
            parts.append(f"👤 Автор: {post.author.first_name} {post.author.last_name}")
        elif isinstance(post.author, VKGroup):
            parts.append(f"👥 Автор: {post.author.name}")

    parts.append(f"🔗 Ссылка: {post.url}")
    
    if post.text:
        parts.append("")
        parts.append(post.text)
    
    return "\n".join(parts)