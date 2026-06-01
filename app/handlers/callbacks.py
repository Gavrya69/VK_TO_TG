from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ChatMemberUpdated
from aiogram.fsm.context import FSMContext

from handlers.menu import get_main_menu, get_delete_menu, get_back_button
from handlers.states import GroupControl
from services.subscriptions import add_vk_group, delete_subscription
from database.db import SessionLocal, get_subscriptions, add_target, get_target

router = Router()

    
@router.callback_query(F.data == "info")
async def handle_info_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Тут инфа про бота",
        reply_markup=get_back_button()
    )
    await callback.answer()
    
@router.callback_query(F.data == "main_menu")
async def handle_info_callback(callback: CallbackQuery, state: FSMContext):
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
        "Отправь ссылку на VK группу",
        reply_markup=get_back_button()
    )
    
    await callback.answer()

@router.message(GroupControl.waiting_for_add)
async def process_group(message: Message, state: FSMContext):
    link = message.text
    user_id = message.from_user.id
    
    async with SessionLocal() as session:
        result = await add_vk_group(session=session, link=link, user_id=user_id)
        
    if result == "unfound":
        await message.answer(
            f"По данной ссылке не найдено группы.",
            reply_markup=get_main_menu()
        )
    elif result == "closed":
        await message.answer(
            f"Данная группа является закрытой.",
            reply_markup=get_main_menu()
        )
    elif result == "subscribed":        
        await message.answer(
            f"Ты уже подписан на эту группу.",
            reply_markup=get_main_menu()
        )
    elif result == "ok":
        await message.answer(
            f"Ты успешно подписался на данную группу.",
            reply_markup=get_main_menu()
        )
        
    await state.clear()
        
    
@router.callback_query(F.data == "del_group")
async def add_group_callback(callback: CallbackQuery, state: FSMContext):

    async with SessionLocal() as session:
        subscriptions = await get_subscriptions(
            session=session,
            user_id=callback.from_user.id
        )    
    if subscriptions:
        await callback.message.edit_text(
            "Выбери группу:",
            reply_markup=get_delete_menu(subscriptions)
        )
        await callback.answer()
    else:        
        await callback.answer("У тебя нет групп")

@router.callback_query(F.data.startswith("del_group:"))
async def delete_subscription_callback(callback: CallbackQuery):
    group_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        await delete_subscription(
            session=session,
            user_id=callback.from_user.id,
            group_id=group_id
        )
        subscriptions = await get_subscriptions(
            session=session,
            user_id=callback.from_user.id
        )   

    await callback.message.edit_text(
        "Выбери группу:",
        reply_markup=get_delete_menu(subscriptions)
    )
    await callback.answer("Подписка удалена")


@router.my_chat_member()
async def bot_added(event: ChatMemberUpdated):

    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    if old_status in (
        "left",
        "kicked"
    ) and new_status in (
        "member",
        "administrator"
    ):

        async with SessionLocal() as session:
            target = await get_target(
                session=session,
                chat_id=event.chat.id
            )
            if target:
                return

            await add_target(
                session=session,
                owner_id=event.from_user.id,
                chat_id=event.chat.id,
                title=event.chat.title,
                chat_type=event.chat.type,
            )