import asyncio

from services.vk.client import vk
from database.db import (
    SessionLocal,
    get_groups,
    get_bindings_by_group,
    update_binding_last_post_id,
    update_group_last_post_id,
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
                        ref=group.screen_name,
                        last_post_id=group.last_post_id
                    )
                    
                    if not result["ok"]:
                        continue
                    
                    posts = result["posts"]
                    for p in posts: print(p.id) #============================================
                    if not posts:
                        continue
                    
                    bindings = await get_bindings_by_group(
                        session=session,
                        vk_group_id=group.vk_group_id
                    )
                    
                    for binding in bindings:
                        binding_posts = [post for post in posts if {
                            binding.last_post_id is None or
                            post.id > binding.last_post_id
                        }]
                        
                        if not binding_posts:
                            continue
                        
                        for binding_post in binding_posts:
                            text = format_post(binding_post)
                            chunks = split_post(text)
                            
                            for chunk in chunks:
                                await bot.send_message(
                                    binding.telegram_chat_id,
                                    chunk,
                                )
                            
                            await update_binding_last_post_id(
                                session=session,
                                vk_group_id=binding.vk_group_id,
                                telegram_chat_id=binding.telegram_chat_id,
                                last_post_id=binding_post.id,
                            )
                            
                    await update_group_last_post_id(
                        session=session,
                        group_id=group.id,
                        last_post_id=posts[-1].id,
                    )
        
        except Exception as e:
            print("Polling error:", e)
        
        await asyncio.sleep(60)