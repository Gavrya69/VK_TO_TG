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
async def cmd_parse_group(message: Message):
    args = message.text.split(maxsplit=2)
    link = args[1]
    posts_cont = args[2]
    chat_id = message.chat.id
    
    async with VKSession() as vk:
        result = await vk.get_group_posts(link, posts_cont)
        
        if result["ok"]:
            await message.answer(
                "Парсинг постов...",
            )
            posts = (await vk.get_group_posts(link, posts_cont))["response"]["items"]
            for post in posts:
                await message.answer(
                    post["text"],
                )
        else:
            await message.answer(
                result["status"],
            )
    