import logging
import os
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers.callbacks import router as callbacks_router
from handlers.commands import router as commands_router

from database.db import init_db
from services.vk import vk


logger = logging.getLogger(__name__)


async def startup():
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(commands_router)
    dp.include_router(callbacks_router)
    
    await init_db()
    
    @dp.startup()
    async def on_startup() -> None:
        # logger.info("Start.")
        await vk.start()
        

    @dp.shutdown()
    async def on_shutdown() -> None:
        await vk.close()
        # logger.info("Exit.")

    await dp.start_polling(bot)


def main():
    load_dotenv()
    # logging.basicConfig(level=logging.DEBUG)
    asyncio.run(startup())


if __name__ == "__main__":
    main()
