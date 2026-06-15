import asyncio
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from keyboards.menu import (
    get_private_main_menu,
    get_public_main_menu,
    get_chat_menu,
    get_my_chats_menu,
    get_delete_menu,
    get_parse_menu,
)

from keyboards.buttons import get_back_button
from handlers.states import GroupControl

from services.tg import sync_chat_admins, format_post
from services.vk.client import vk
from utils import split_post

from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_binding,
    get_bindings_by_chat,
    get_bindings_with_groups,
    delete_binding,
    get_chats,
    delete_chat_admins,
    add_chat,
    get_chats_by_admin,
    get_chat,
)

router = Router()

    
@router.callback_query(F.data == "info")
async def info_menu(callback: CallbackQuery):
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
async def back(callback: CallbackQuery, state: FSMContext):
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
    # TODO: Сделать гиперссылки на группы
    await callback.message.edit_text(
        f"Групп привязано к этому чату: {len(bindings)}.",
        reply_markup=get_chat_menu(chat_id)
    )
    
    await callback.answer()
    
    
@router.callback_query(F.data == "my_chats")
async def my_chats_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    # TODO: Сделать гиперссылки на чаты и каналы
    async with SessionLocal() as session:
        chats = await get_chats_by_admin(
            session=session,
            user_id=user_id,
        )
        chat_ids = [c.chat_id for c in chats]
        chats = await get_chats(
            session=session,
            chat_ids=chat_ids
        )
        
    await callback.message.edit_text(
        f"Ваши каналы: {len(chats)}.",
        reply_markup=get_my_chats_menu(chats)
    )
    
    await callback.answer()
    
    
@router.callback_query(F.data.startswith("add_binding:"))
async def add_binding_menu(callback: CallbackQuery, state: FSMContext):
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
    
    result = (await vk.get_group_info(link))
    if not result["ok"]:
        if result["status"] == "not_found":
            await message.answer(
                "Группа не найдена.",
                reply_markup=get_back_button(chat_id)
            )
        elif result["status"] == "access_denied":
            await message.answer(
                "Ошибка доступа к группе.",
                reply_markup=get_back_button(chat_id)
            )
        elif result["status"] == "unknown_error":
            await message.answer(
                "Неизвестная ошибка.",
                reply_markup=get_back_button(chat_id)
            )
        elif result["status"] == "private":
            await message.answer(
                "Группа является приватной.",
                reply_markup=get_back_button(chat_id)
            )
        elif result["status"] == "closed":
            await message.answer(
                "Группа является закрытой.",
                reply_markup=get_back_button(chat_id)
            )
        await state.clear()
        return
        
    group = result["group"]
    
    posts = (await vk.get_group_posts(link))["posts"]
    last_post_id = posts[0].id if posts else 1

    async with SessionLocal() as session:
        chat = await get_chat(session, chat_id)
        if not chat:
            chat = await add_chat(
                session=session,
                chat_id=chat_id,
                title=message.chat.title or "private",
                chat_type=message.chat.type,
            )
        
        db_group = await get_group(session, vk_group_id=group.id)
        if not db_group:
            db_group = await add_group(
                session=session,
                vk_group_id=group.id,
                name=group.name,
                screen_name=group.screen_name,
                last_post_id=last_post_id
            )
        
        binding = await get_binding(session=session, vk_group_id=group.id, telegram_chat_id=chat_id)
        if not binding:
            await add_binding(
                session=session,
                vk_group_id=group.id,
                telegram_chat_id=chat_id,
                last_post_id=last_post_id,
            )
            await message.answer(
                "Привязка успешно создана. Желаете спарсить посты?",
                reply_markup=get_parse_menu(chat_id, group.id)
            )
        else:
            await message.answer(
                "Данная группа уже привязана к этому чату.",
                reply_markup=get_back_button(chat_id)
            )
            
    await state.clear()
    
    
@router.callback_query(F.data.startswith("parse:"))
async def parse_posts(callback: CallbackQuery, state: FSMContext):
    chat_id = int(callback.data.split(":")[1])
    group_id = int(callback.data.split(":")[2])
    
    await state.set_state(GroupControl.waiting_for_post_count)
    await state.update_data(target_chat_id=chat_id)
    await state.update_data(vk_group_id=group_id)

    await callback.message.edit_text(
        "Сколько постов ты хочешь спарсить?",
        reply_markup=get_back_button(chat_id)
    )

    await callback.answer()
    
    
@router.message(GroupControl.waiting_for_post_count)
async def process_parsing(message: Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["target_chat_id"]
    group_id = data["vk_group_id"]

    try:
        posts_count = int(message.text)
    except:
        await message.answer(
            "Введите число",
            reply_markup=get_back_button()
        )
        return
    
    loading_msg = await message.answer(
        "⏳ Подождите, начинаю работу...\nЭто сообщение удалится при завершении.",
    )
    
    result = await vk.get_group_posts(group_id, posts_count)
    
    if result["ok"]:
        posts = result["posts"]
        
        if not posts:        
            await loading_msg.edit_text(
                f"В данной группе нет постов.",
                reply_markup=get_back_button("main_menu")
            )
            return
        
        for post in posts:
            text = format_post(post)
            chunks = split_post(text)
            
            for chunk in chunks:
                await message.answer(
                    chunk,
                )
                
        await loading_msg.delete()
        
    else:
        await loading_msg.edit_text(
            f"Ошибка: {result['status']}",
            reply_markup=get_back_button("main_menu")
        )

    
@router.callback_query(F.data.startswith("del_binding_menu:"))
async def del_binding_menu(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        bindings = await get_bindings_with_groups(
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
async def del_binding(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    vk_group_id = int(callback.data.split(":")[2])

    async with SessionLocal() as session:
        await delete_binding(
            session=session,
            vk_group_id=vk_group_id,
            telegram_chat_id=chat_id,
        )
        bindings = await get_bindings_with_groups(
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