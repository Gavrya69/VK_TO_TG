from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from handlers.menu import get_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):

    await message.answer(
        "VK → TG бот. Добавь бота в чат и настрой источники через меню.",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start - запуск\n"
        "/help - помощь\n\n"
        "Управление происходит через меню."
    )