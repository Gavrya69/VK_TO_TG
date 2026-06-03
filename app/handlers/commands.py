from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from handlers.menu import get_private_main_menu, get_chat_main_menu, get_delete_menu, get_close_button
from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_binding,
    get_bindings_by_chat,
    delete_binding,
    delete_chat_admins,
    add_chat,
    get_chat,
)


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if message.chat.type == "private":
        markup = get_private_main_menu()
    else:
        markup = get_chat_main_menu()
        
    await message.answer(
        "Главное меню:",
        reply_markup=markup
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - запуск\n"
        "/help - помощь\n\n"
        "/add"
    )
    
    
@router.message(Command("add"))
async def cmd_add_group(message: Message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer(
            "Использование:\n/add https://vk.com/group",
            reply_markup=get_close_button()
        )
        return
    
    link = args[1]
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
                reply_markup=get_close_button()
            )
        else:
            await message.answer(
                "Данная группа уже привязана к этому чату.",
                reply_markup=get_close_button()
            )
    
    
@router.message(Command("delete"))
async def cmd_delete_group(message: Message):
    chat_id = message.chat.id

    async with SessionLocal() as session:
        bindings = await get_bindings_by_chat(
            session=session,
            telegram_chat_id=chat_id,
        )
    
    if bindings:
        await message.answer(
            "Какую группу хотите удалить?",
            reply_markup=get_delete_menu(bindings, menu_button=False)
        )
    else:
        await message.answer(
            "Здесь нет групп.",
            reply_markup=get_close_button()
        )
    