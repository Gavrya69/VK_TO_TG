from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InputMediaPhoto

from services.vk.client import vk
from keyboards.menu import get_private_main_menu, get_public_main_menu
from keyboards.buttons import get_close_button
from services.tg import format_post, send_post

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
async def cmd_get_posts(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) <= 1:
        await message.answer(
            "Использование команды:\n/get_posts <ссылка на группу> <количество постов>",
            reply_markup=get_close_button()
            )
        return
    
    loading_msg = await message.answer(
        "⏳ Подождите, начинаю работу...\nЭто сообщение удалится при завершении.",
    )
    
    link = args[1]
    try:
        count = int(args[2])
    except ValueError:
        await message.answer(
            "Использование команды:\n/get_posts <ссылка на группу> <количество постов>",
            reply_markup=get_close_button()
            )
        return
        
    count = max(1, min(count, 50))
    result = await vk.get_group_posts(link, count)
    
    if result["ok"]:
        posts = result["posts"]
        
        if not posts:        
            await loading_msg.edit_text(
                f"В данной группе нет постов.",
                reply_markup=get_close_button()
            )
            return
        
        for post in posts:
            await send_post(
                bot=message.bot,
                chat_id=message.chat.id,
                post=post
            )
        
        await loading_msg.delete()
        
    else:
        await loading_msg.edit_text(
            f"Ошибка: {result['status']}",
            reply_markup=get_close_button()
        )


@router.message(Command("get_pinned"))
async def cmd_parse_group(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) <= 1:
        await message.answer(
            "Использование команды:\n/get_pinned <ссылка на группу>",
            reply_markup=get_close_button()
            )
        return
    
    loading_msg = await message.answer(
        "⏳ Подождите, начинаю работу...\nЭто сообщение удалится при завершении.",
    )
    
    link = args[1]    
    result = await vk.get_group_posts(link, 5, with_pinned=True)
    
    if result["ok"]:
        posts = result["posts"]
        pinned_posts = [post for post in posts if post.get("is_pinned")]
        
        if not pinned_posts:        
            await loading_msg.edit_text(
                f"В данной группе нет закрепленных постов.",
                reply_markup=get_close_button()
            )
            return
        
        for post in pinned_posts:
            await send_post(
                bot=message.bot,
                chat_id=message.chat.id,
                post=post
            )
        
        await loading_msg.delete()
    else:
        await loading_msg.edit_text(
            f"Ошибка: {result['status']}",
            reply_markup=get_close_button()
        )


@router.message(Command("some_command"))
async def cmd_some_command(message: Message):
    # TODO: Тут будет какая-нибудь некст команда
    pass