from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext

from handlers.menu import get_main_menu, get_delete_menu, get_back_button
from handlers.states import GroupControl

from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_bindings_by_chat,
    delete_binding,
    add_chat,
    get_chat,
)

router = Router()

    
@router.callback_query(F.data == "info")
async def handle_info_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "VK → TG бот. Перенос постов из VK в Telegram.",
        reply_markup=get_back_button()
    )
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=get_main_menu()
    )

    await callback.answer()
    
    
    
    
@router.callback_query(F.data == "add_group")
async def add_group_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GroupControl.waiting_for_add)

    await callback.message.edit_text(
        "Отправь VK ссылку (например vk.com/habr)",
        reply_markup=get_back_button()
    )

    await callback.answer()
    
    
@router.message(GroupControl.waiting_for_add)
async def process_group(message: Message, state: FSMContext):
    link = message.text
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
            
        await add_binding(
            session=session,
            vk_group_id=group.vk_group_id,
            telegram_chat_id=chat.telegram_chat_id,
        )

    await message.answer(
        "Привязка создана.",
        reply_markup=get_main_menu()
    )

    await state.clear()
    
    
@router.message(GroupControl.waiting_for_add)
async def process_group(message: Message, state: FSMContext):
    link = message.text
    chat_id = message.chat.id

    async with SessionLocal() as session:

        # 1. получаем или создаём чат
        chat = await get_chat(session, chat_id)

        if not chat:
            chat = await add_chat(
                session=session,
                chat_id=chat_id,
                title=message.chat.title or "private",
                chat_type=message.chat.type,
            )

        # 2. создаём VK группу (упрощённо — пока без API резолва)
        group = await get_group(session, vk_group_id=link)

        if not group:
            group = await add_group(
                session=session,
                vk_group_id=link,
                name=link,
            )

        # 3. создаём binding
        await add_binding(
            session=session,
            vk_group_id=group.vk_group_id,
            telegram_chat_id=chat.telegram_chat_id,
        )

    await message.answer(
        "Привязка создана.",
        reply_markup=get_main_menu()
    )

    await state.clear()
    
    
@router.callback_query(F.data.startswith("del_group:"))
async def delete_binding_callback(callback: CallbackQuery):

    vk_group_id = int(callback.data.split(":")[1])
    chat_id = callback.message.chat.id

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

    await callback.message.edit_text(
        "Обновлённый список:",
        reply_markup=get_delete_menu(bindings)
    )

    await callback.answer("Удалено")
    
    
    
@router.my_chat_member()
async def bot_added(event: ChatMemberUpdated):

    old = event.old_chat_member.status
    new = event.new_chat_member.status

    if old in ("left", "kicked") and new in ("member", "administrator"):

        async with SessionLocal() as session:

            chat = await get_chat(
                session=session,
                chat_id=event.chat.id
            )

            if chat:
                return

            await add_chat(
                session=session,
                chat_id=event.chat.id,
                title=event.chat.title or "unknown",
                chat_type=event.chat.type,
            )