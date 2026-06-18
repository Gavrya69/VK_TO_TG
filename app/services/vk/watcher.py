import asyncio

from services.vk.client import vk
from database.db import (
    SessionLocal,
    get_groups,
    get_bindings_by_group,
    get_min_last_post_id,
    update_binding_last_post_id,
    update_group_last_post_id,
)
from services.tg import send_post


async def poll_vk(bot):
    while True:
        try:
            async with SessionLocal() as session:
                groups = await get_groups(session)
                
                for group in groups:
                    min_last_post_id = await get_min_last_post_id(
                        session=session,
                        vk_group_id=group.vk_group_id
                    )
                    if min_last_post_id is None:
                        continue
                    result = await vk.get_new_posts(
                        ref=group.screen_name,
                        last_post_id=min_last_post_id
                    )
                    
                    if not result["ok"]:
                        continue
                    
                    posts = result["posts"]
                    
                    if not posts:
                        continue
                    
                    bindings = await get_bindings_by_group(
                        session=session,
                        vk_group_id=group.vk_group_id
                    )
                    
                    for binding in bindings:
                        binding_posts = [post for post in posts if 
                            binding.last_post_id is None
                            or post.id > binding.last_post_id
                        ]
                        
                        if not binding_posts:
                            continue
                        
                        for binding_post in binding_posts:
                            await send_post(
                                bot=bot,
                                chat_id=binding.tg_chat_id,
                                post=binding_post
                            )
                            await update_binding_last_post_id(
                                session=session,
                                vk_group_id=binding.vk_group_id,
                                tg_chat_id=binding.tg_chat_id,
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