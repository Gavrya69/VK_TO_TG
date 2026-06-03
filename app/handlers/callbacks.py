import asyncio
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext

from handlers.menu import (
    get_private_main_menu,
    get_chat_main_menu,
    get_back_button,
    get_this_chat_menu,
    get_my_chats_menu,
    get_delete_menu,
    get_close_button
)

from handlers.states import GroupControl
from services import sync_chat_admins  

from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_binding,
    get_bindings_by_chat,
    delete_binding,
    get_chats,
    delete_chat_admins,
    add_chat,
    get_chats_by_admin,
    get_chat,
)

router = Router()

    
@router.callback_query(F.data == "info")
async def handle_info_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Перенос постов из VK групп в Telegram каналы и чаты.",
        reply_markup=get_back_button("main_menu")
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message.chat.type == "private":
        markup = get_private_main_menu()
    else:
        markup = get_chat_main_menu()
        
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=markup
    )

    await callback.answer()

@router.callback_query(F.data.startswith("back:"))
async def back_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    target = callback.data.split(":", 1)[1]

    if target == "main_menu":
        await main_menu(callback, state)
        
    elif target == "this_chat":
        await this_chat_menu(callback, state)
        
    elif target == "my_groups":
        pass
        
    await callback.answer()


@router.callback_query(F.data == "close")
async def close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.delete()
    
    await callback.answer()
    
    
@router.callback_query(F.data == "this_chat")
async def this_chat_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = callback.message.chat.id

    async with SessionLocal() as session:
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
    # print(gid.vk_group_id for gid in bindings])
    await callback.message.edit_text(
        f"Групп привязано к этому чату: {len(bindings)}.",
        reply_markup=get_this_chat_menu()
    )
    
    await callback.answer()
    
    
@router.callback_query(F.data == "my_chats")
async def my_chats_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id

    async with SessionLocal() as session:
        chats = await get_chats_by_admin(
            session=session,
            user_id=user_id,
        )
        print(chats)
        chat_ids = [c.chat_id for c in chats]
        chats = await get_chats(
            session=session,
            chat_ids=chat_ids)
        print(chats)
    await callback.message.edit_text(
        f"Ваши каналы: {len(chats)}.",
        reply_markup=get_my_chats_menu(chats)
    )
    
    await callback.answer()
    
@router.callback_query(F.data == "add_group")
async def add_group_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GroupControl.waiting_for_add)

    await callback.message.edit_text(
        "Отправь VK ссылку (например vk.com/habr)",
        reply_markup=get_back_button("this_chat")
    )

    await callback.answer()
    
    
@router.message(GroupControl.waiting_for_add)
async def process_group(message: Message, state: FSMContext):
    link = int(message.text)
    chat_id = message.chat.id
    
    async with SessionLocal() as session:
        chat = await get_chat(session, chat_id)
        if not chat:
            chat = await add_chat(
                session=session,
                chat_id=chat_id,
                title=message.chat.title or "private",
                chat_type=message.chat.type,
            )
            
        group = await get_group(session, vk_group_id=link)
        if not group:
            group = await add_group(
                session=session,
                vk_group_id=link,
                name=link,
            )
        
        binding = await get_binding(session, vk_group_id=link, telegram_chat_id=chat_id)
        if not binding:
            await add_binding(
                session=session,
                vk_group_id=link,
                telegram_chat_id=chat_id,
            )
            await message.answer(
                "Привязка создана.",
                reply_markup=get_back_button("this_chat")
            )
        else:
            await message.answer(
                "Данная группа уже привязана к этому чату.",
                reply_markup=get_back_button("this_chat")
            )
            
    await state.clear()
    
    
@router.callback_query(F.data == "del_group")
async def delete_binding_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id

    async with SessionLocal() as session:
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
    
    if bindings:
        await callback.message.edit_text(
            "Какую группу хотите удалить?",
            reply_markup=get_delete_menu(bindings)
        )
    else:
        await callback.answer("К этому чату не привязаны группы.")
    
    await callback.answer()
    
    
@router.callback_query(F.data.startswith("del_group_menu:"))
async def delete_binding_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    vk_group_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        await delete_binding(
            session=session,
            vk_group_id=vk_group_id,
            telegram_chat_id=chat_id,
        )
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )

    if bindings:
        await callback.message.edit_text(
            "Какую группу хотите удалить?",
            reply_markup=get_delete_menu(bindings, back_button=True)
        )
    else:
        await callback.message.edit_text(
            "Здесь нет групп.",
            reply_markup=get_delete_menu(bindings, back_button=True)
        )

    await callback.answer("Удалено")
    
    
@router.callback_query(F.data.startswith("del_group_chat:"))
async def delete_binding_callback(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    vk_group_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        await delete_binding(
            session=session,
            vk_group_id=vk_group_id,
            telegram_chat_id=chat_id,
        )
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
        
    if bindings:
        await callback.message.edit_text(
            "Какую группу хотите удалить?",
            reply_markup=get_delete_menu(bindings, back_button=False)
        )
    else:
        await callback.message.edit_text(
            "Здесь нет групп.",
            reply_markup=get_delete_menu(bindings, back_button=False)
        )

    await callback.answer("Удалено")
    

    
@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated, bot):
    chat_id = event.chat.id
    
    async with SessionLocal() as session:
        chat = await get_chat(session, chat_id)

        if not chat:
            chat = await add_chat(
                session=session,
                chat_id=chat_id,
                title=event.chat.title or "unknown",
                chat_type=event.chat.type,
            )
            
        old = event.old_chat_member.status
        new = event.new_chat_member.status
    
        if old in ("left", "kicked") and new in ("member", "administrator"):
            await asyncio.sleep(2) # for sync
            await sync_chat_admins(
                bot=bot,
                session=session,
                chat_id=chat_id,
            )
        elif new in ("left", "kicked"):
            await asyncio.sleep(2) # for sync
            await delete_chat_admins(session=session, chat_id=chat_id)