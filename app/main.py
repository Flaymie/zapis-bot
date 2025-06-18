import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import BOT_TOKEN
from app.handlers import register_handlers

# Инициализация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Функция запуска бота
async def main():
    # Инициализация планировщика задач
    scheduler = AsyncIOScheduler()
    
    # Инициализация хранилища состояний
    storage = MemoryStorage()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Регистрация обработчиков
    db = register_handlers(dp, bot, scheduler)
    
    # Запуск планировщика
    scheduler.start()
    
    # Включаем режим пропуска обновлений
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        # Запуск поллинга
        await dp.start_polling(bot)
    finally:
        # Корректное завершение работы
        await bot.session.close()
        scheduler.shutdown()

if __name__ == "__main__":
    # Запуск бота
    asyncio.run(main())
