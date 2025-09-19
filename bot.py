import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from database import init_db
from handlers import router

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set in environment")
        return

    # Initialize storage for FSM
    storage = MemoryStorage()
    
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await init_db()

    try:
        logger.info("Starting bot polling")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Exception while polling: %s", e)


if __name__ == "__main__":
    asyncio.run(main())
