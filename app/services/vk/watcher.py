import asyncio

from services.vk.client import vk
from database.db import (
    SessionLocal,
    get_groups,
    update_last_post_id,
    get_bindings_by_group,
)
from services.tg import format_post
from utils import split_post


async def poll_vk(bot):
    while True:
        try:
            async with SessionLocal() as session:
                groups = await get_groups(session)
                
                for group in groups:
                    result = await vk.get_new_posts(
                        group.screen_name,
                        group.last_post_id
                    )
                    
                    if not result["ok"]:
                        continue
                    
                    posts = result["posts"]
                    
                    if not posts:
                        continue
                    
                    bindings = await get_bindings_by_group(
                        session,
                        group.vk_group_id
                    )
                    
                    for post in posts:
                        text = format_post(post)
                        chunks = split_post(text)
                        
                        for binding in bindings:
                            for chunk in chunks:
                                await bot.send_message(
                                    binding.telegram_chat_id,
                                    chunk,
                                )
                        
                            await update_last_post_id(
                                session,
                                group.id,
                                posts[-1].id,
                            )

        except Exception as e:
            print("Polling error:", e)

        await asyncio.sleep(60)