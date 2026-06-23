import asyncio

from aiogram import Bot
from aiogram.types import InputMediaPhoto
from aiogram.exceptions import TelegramRetryAfter
from sqlalchemy.ext.asyncio import AsyncSession

from services.vk.client import vk
from services.downloader import downloader
from services.vk.models import VKPost, VKUser, VKGroup
from database.db import add_chat_admin, delete_chat_admins
from utils import split_post


async def update_user_chats(
    bot,
    session: AsyncSession,
    db_chats: list[int],
):
    updated = 0
    
    for db_chat in db_chats:
        try:
            tg_chat = await bot.get_chat(db_chat.chat_id)
            
            if db_chat.name != tg_chat.name:
                db_chat.name = tg_chat.name
                updated += 1
            
        except Exception:
            continue
    
    if updated:
        await session.commit()
    
    return updated


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


async def send_post(
    bot: Bot,
    chat_id: int,
    post: VKPost,
) -> None:
    text = format_post(post) or ""
    
    media_raw = []
    
    for url in post.photos:
        try:
            media_raw.append(await downloader.download_image(url))
        except Exception as e:
            print(f"Photo download failed: {url} -> {e}")
    
    if not media_raw:
        for chunk in split_post(text):
            while True:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=chunk
                    )
                    break
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
        return
    
    chunks = split_post(text, first_limit=1024) or [""]
    
    media = [
        InputMediaPhoto(
            media=media_raw[0],
            caption=chunks[0]
        )
    ]
    
    for photo in media_raw[1:10]:
        media.append(
            InputMediaPhoto(media=photo)
        )
    
    if len(media) == 1:
        while True:
            try:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=media[0].media,
                    caption=media[0].caption
                )
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
    else:
        while True:
            try:
                await bot.send_media_group(
                    chat_id=chat_id,
                    media=media
                )
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
    
    for chunk in chunks[1:]:
        while True:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=chunk
            )
                break
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
    
    await asyncio.sleep(0.1)