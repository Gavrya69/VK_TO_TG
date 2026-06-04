import asyncio
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext

from keyboards.menu import (
    get_private_main_menu,
    get_public_main_menu,
    get_chat_menu,
    get_my_chats_menu,
    get_delete_menu,
)

from keyboards.buttons import get_back_button
from handlers.states import GroupControl

from services.tg import sync_chat_admins
from services.vk import VKSession

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
    chat_id = callback.message.chat.id
    
    if callback.message.chat.type == "private":
        markup = get_private_main_menu(chat_id)
    else:
        markup = get_public_main_menu(chat_id)
        
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
    else :
        await chat_menu(callback, state)
        
    await callback.answer()


@router.callback_query(F.data == "close")
async def close(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.delete()
    
    await callback.answer()
    
    
@router.callback_query(F.data.startswith("chat_menu:"))
async def chat_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
    # print(gid.vk_group_id for gid in bindings])
    await callback.message.edit_text(
        f"Групп привязано к этому чату: {len(bindings)}.",
        reply_markup=get_chat_menu(chat_id)
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
        chat_ids = [c.chat_id for c in chats]
        chats = await get_chats(
            session=session,
            chat_ids=chat_ids)
        
    await callback.message.edit_text(
        f"Ваши каналы: {len(chats)}.",
        reply_markup=get_my_chats_menu(chats)
    )
    
    await callback.answer()
    
@router.callback_query(F.data.startswith("add_binding:"))
async def add_binding_callback(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    
    await state.set_state(GroupControl.waiting_for_add)
    await state.update_data(target_chat_id=chat_id)

    await callback.message.edit_text(
        "Отправь VK ссылку (например vk.com/habr)",
        reply_markup=get_back_button(chat_id)
    )

    await callback.answer()
    
    
@router.message(GroupControl.waiting_for_add)
async def process_binding(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["target_chat_id"]
    link = message.text
    
    async with VKSession() as vk:
        resp = (await vk.check_group_by_link(link))
        if not resp["ok"]:
            if resp["status"] == "not_found":
                await message.answer(
                    "Группа не найдена.",
                    reply_markup=get_back_button(chat_id)
                )
            elif resp["status"] == "access_denied":
                await message.answer(
                    "Ошибка доступа к группе.",
                    reply_markup=get_back_button(chat_id)
                )
            elif resp["status"] == "unknown_error":
                await message.answer(
                    "Неизвестая ошибка.",
                    reply_markup=get_back_button(chat_id)
                )
            elif resp["status"] == "private":
                await message.answer(
                    "Группа является приватной.",
                    reply_markup=get_back_button(chat_id)
                )
            elif resp["status"] == "closed":
                await message.answer(
                    "Группа является закрытой.",
                    reply_markup=get_back_button(chat_id)
                )
            await state.clear()
            return
        
        info = resp["group"]
    
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
                vk_group_id=info["id"],
                name=info["name"],
                screen_name=info["screen_name"],
                url=f"https://vk.com/{info['screen_name']}",
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
                reply_markup=get_back_button(chat_id)
            )
        else:
            await message.answer(
                "Данная группа уже привязана к этому чату.",
                reply_markup=get_back_button(chat_id)
            )
            
    await state.clear()
    
    
@router.callback_query(F.data.startswith("del_binding_menu:"))
async def delete_binding_callback(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
    
    if bindings:
        await callback.message.edit_text(
            "Какую группу хотите удалить?",
            reply_markup=get_delete_menu(chat_id, bindings)
        )
    else:
        await callback.answer("К этому чату не привязаны группы.")
    
    await callback.answer()
    
    
@router.callback_query(F.data.startswith("del_binding:"))
async def delete_binding_callback(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    vk_group_id = int(callback.data.split(":")[2])

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
            reply_markup=get_delete_menu(chat_id, bindings)
        )
    else:
        await callback.message.edit_text(
            "Здесь нет групп.",
            reply_markup=get_delete_menu(chat_id, bindings)
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
            reply_markup=get_delete_menu(chat_id, bindings, False)
        )
    else:
        await callback.message.edit_text(
            "Здесь нет групп.",
            reply_markup=get_delete_menu(chat_id, bindings, False)
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