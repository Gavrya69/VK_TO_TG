from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from handlers.menu import get_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
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
    
    