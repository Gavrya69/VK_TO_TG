from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from handlers.menu import get_main_menu
from database.db import SessionLocal, add_user, check_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    
    async with SessionLocal() as session:
        user_exist = await check_user(
            session=session,
            user_id=message.from_user.id
        )
        if not user_exist:
            await add_user(
                session=session,
                user_id=message.from_user.id
            )
            await message.answer(
                "Даров, я кароче парсить буду вк."
            )
        
    await message.answer(
        "Главное меню:\n",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - Запуск бота\n"
        "/help - Показать доступные команды"
    )


# @router.message(Command("connect")):
# async def cmd_connect(message: Message):
#     pass