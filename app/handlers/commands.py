from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from services.vk import vk
from keyboards.menu import get_private_main_menu, get_public_main_menu
from keyboards.buttons import get_close_button
from services.tg import add_post_info

from database.db import (
    SessionLocal,
    add_group,
    get_group,
    add_binding,
    get_binding,
    add_chat,
    get_chat,
)

from utils import split_post



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
    
    
@router.message(Command("get_posts"))
async def cmd_parse_group(message: Message):
    args = message.text.split(maxsplit=2)
    link = args[1]
    count = args[2]
    chat_id = message.chat.id
    
    result = await vk.get_group_posts(link, count)
    
    if result["ok"]:
        # TODO: Удалять это сообщение в конце
        await message.answer(
            "Подождите, происходит парсинг постов...\nЭто сообщение удалится при завершении.",
    )
        posts = result["posts"]
        # TODO: Добавить ответ когда нет постов
        for post in posts:
            chunks = split_post(post["text"])
            
            for chunk in chunks:
                chunk = add_post_info(chunk)
                await message.answer(
                    chunk,
                )
    else:
        await message.answer(
            result["status"]
        )
    

@router.message(Command("get_pinned"))
async def cmd_parse_group(message: Message):
    args = message.text.split(maxsplit=2)
    link = args[1]
    count = args[2]
    chat_id = message.chat.id
    
    result = await vk.get_group_posts(link, count, with_pinned=True)
    
    if result["ok"]:
        posts = result["posts"]
        pinned_posts = [post for post in posts if post.get("is_pinned")]
        # TODO: Добавить ответ когда нет постов
        for post in pinned_posts:
            chunks = split_post(post["text"])
            
            for chunk in chunks:
                await message.answer(
                    chunk,
                )
    else:
        await message.answer(
            result["status"],
        )
    