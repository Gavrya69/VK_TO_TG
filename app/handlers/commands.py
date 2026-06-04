from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from services.vk import VKSession
from keyboards.menu import get_private_main_menu, get_public_main_menu
from keyboards.buttons import get_close_button

from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_binding,
    add_chat,
    get_chat,
)


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    chat_id = message.chat.id
    
    if message.chat.type == "private":
        markup = get_private_main_menu(chat_id)
    else:
        markup = get_public_main_menu(chat_id)
        
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
    
    
@router.message(Command("parse"))
async def cmd_addroup(message: Message):
    args = message.text.split(maxsplit=1)
    link = args[1]
    walls_count = args[2]
    chat_id = message.chat.id
    
    async with VKSession() as vk:
        resp = (await vk.get_group_info(link))
    
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
    