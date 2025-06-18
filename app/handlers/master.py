import logging
from aiogram import Router, types
from aiogram.filters import Command

from app.utils.helpers import format_master_info

# Создаем роутер для команд мастеров
router = Router()

# Инициализируем сервисы
db = None

def init_services(database):
    """Функция для инициализации сервисов при старте бота"""
    global db
    db = database

# Просмотр мастером своих записей
@router.message(Command("my_appointments"))
async def my_appointments_handler(message: types.Message):
    try:
        # Проверяем, является ли пользователь мастером
        master = db.get_master_by_telegram_id(message.from_user.id)
        if not master:
            await message.answer("⚠️ Вы не зарегистрированы как мастер.")
            return

        # Получаем все предстоящие записи
        appointments = db.get_upcoming_appointments_for_master(master[0])
        
        if not appointments:
            await message.answer("📭 У вас нет предстоящих записей.")
            return

        # Формируем список записей
        text = f"👨‍🔧 {format_master_info(master)}\n📋 Ваши предстоящие записи:\n\n"
        
        # Группируем записи по дате
        appointments_by_date = {}
        for app in appointments:
            date = app[1]
            if date not in appointments_by_date:
                appointments_by_date[date] = []
            appointments_by_date[date].append(app)
        
        # Выводим записи сгруппированные по датам
        for date, apps in sorted(appointments_by_date.items()):
            text += f"📅 {date}:\n"
            for app in sorted(apps, key=lambda x: x[2]):  # Сортируем по времени
                text += (
                    f"⏰ {app[2]} - {app[3]}\n"
                    f"👤 Клиент: ID {app[4]}\n"
                    f"🔑 ID записи: {app[0]}\n"
                )
            text += "━━━━━━━━━━━━━━\n"

        await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра записей мастера: {e}")
        await message.answer("⚠️ Не удалось загрузить записи.")

# Просмотр сегодняшних записей
@router.message(Command("today"))
async def today_appointments_handler(message: types.Message):
    try:
        # Проверяем, является ли пользователь мастером
        master = db.get_master_by_telegram_id(message.from_user.id)
        if not master:
            await message.answer("⚠️ Вы не зарегистрированы как мастер.")
            return

        # Получаем сегодняшние записи
        appointments = db.get_today_appointments_for_master(master[0])
        
        if not appointments:
            await message.answer("📭 У вас нет записей на сегодня.")
            return

        # Формируем список записей
        text = f"👨‍🔧 {format_master_info(master)}\n📋 Ваши записи на сегодня:\n\n"
        
        for app in sorted(appointments, key=lambda x: x[3]):  # Сортируем по времени
            text += (
                f"⏰ {app[3]} - {app[2]}\n"
                f"👤 Клиент: ID {app[1]}\n"
                f"🔑 ID записи: {app[0]}\n"
                "━━━━━━━━━━━━━━\n"
            )

        await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра сегодняшних записей: {e}")
        await message.answer("⚠️ Не удалось загрузить записи на сегодня.")
