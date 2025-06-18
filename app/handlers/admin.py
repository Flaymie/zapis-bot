import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.config import ADMIN_ID
from app.models.states import AdminStates
from app.keyboards.admin_kb import (
    get_admin_main_kb, 
    get_admin_masters_kb, 
    get_admin_reviews_kb,
    get_admin_review_detail_kb,
    get_admin_back_kb
)
from app.services.appointment import AppointmentService
from app.services.review import ReviewService
from app.utils.helpers import get_user_info, format_master_info

# Создаем роутер для команд администратора
router = Router()

# Инициализируем сервисы (они будут переданы при регистрации роутера)
appointment_service = None
review_service = None
db = None
bot = None

def init_services(appointment_svc, review_svc, database, bot_instance):
    """Функция для инициализации сервисов при старте бота"""
    global appointment_service, review_service, db, bot
    appointment_service = appointment_svc
    review_service = review_svc
    db = database
    bot = bot_instance

# Проверка прав администратора
def is_admin(message: types.Message):
    return message.from_user.id == ADMIN_ID

# Главное меню администратора
@router.message(Command("admin"))
async def admin_handler(message: types.Message):
    if not is_admin(message):
        return

    try:
        await message.answer(
            "🔐 Админ-панель\n"
            "Выберите действие:",
            reply_markup=get_admin_main_kb()
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике admin: {e}")
        await message.answer("⚠️ Ошибка админ-панели")

# Показ записей по услуге
@router.callback_query(F.data.startswith("admin_service_"))
async def admin_service_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Извлекаем название услуги
        service = callback.data.split("_")[2]
        appointments = db.get_appointments_by_service(service)

        if not appointments:
            await callback.answer("📭 Нет записей")
            return

        # Формируем текст с записями
        text = "📋 Список записей:\n\n"
        for app in appointments:
            master = db.get_master_by_id(app[5]) if len(app) > 5 else None
            master_info = f"👨‍🔧 Мастер: {format_master_info(master)}\n" if master else ""
            
            text += (
                f"🔑 ID: {app[0]}\n"
                f"👤 User ID: {app[1]}\n"
                f"💅 Услуга: {app[2]}\n"
                f"{master_info}"
                f"📅 Дата: {app[3]}\n"
                f"⏰ Время: {app[4]}\n"
                "━━━━━━━━━━━━━━\n"
            )

        # Выводим с кнопкой Назад
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_back_kb()
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра записей по услуге: {e}")
        await callback.answer("⚠️ Ошибка загрузки записей")

# Управление мастерами
@router.callback_query(F.data == "admin_masters")
async def admin_masters_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Получаем список всех мастеров
        masters = db.get_all_masters()

        if not masters:
            text = "👨‍🔧 Список мастеров пуст."
        else:
            # Формируем текст с мастерами
            text = "👨‍🔧 Список мастеров:\n\n"
            for master in masters:
                username = f" (@{master[5]})" if master[5] else ""
                text += (
                    f"🔑 ID: {master[0]}\n"
                    f"👤 Имя: {master[1]} {master[2]}{username}\n"
                    f"💅 Услуга: {master[3]}\n"
                    f"🆔 TG ID: {master[4]}\n"
                    "━━━━━━━━━━━━━━\n"
                )

        # Отображаем с кнопками управления
        await callback.message.edit_text(
            text, 
            reply_markup=get_admin_masters_kb()
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике управления мастерами: {e}")
        await callback.answer("⚠️ Ошибка загрузки мастеров")

# Добавление мастера - запрос имени
@router.callback_query(F.data == "admin_add_master")
async def admin_add_master_handler(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.message):
        return

    await callback.message.answer("Введите имя и фамилию мастера (например, Иван Иванов):")
    await state.set_state(AdminStates.adding_master_name)

# Добавление мастера - получение имени и запрос услуги
@router.message(AdminStates.adding_master_name)
async def admin_add_master_name_handler(message: types.Message, state: FSMContext):
    if not is_admin(message):
        return

    try:
        # Разбиваем имя и фамилию
        full_name = message.text.strip().split()
        if len(full_name) != 2:
            await message.answer("⚠ Введите имя и фамилию через пробел")
            return

        # Сохраняем имя и фамилию
        first_name, last_name = full_name
        await state.update_data(first_name=first_name, last_name=last_name)
        
        # Запрашиваем услугу
        await message.answer("Введите услугу, которую выполняет мастер (например, Маникюр):")
        await state.set_state(AdminStates.adding_master_service)
    except Exception as e:
        logging.error(f"Ошибка в обработчике добавления имени мастера: {e}")
        await message.answer("⚠ Ошибка ввода имени")

# Добавление мастера - получение услуги и запрос Telegram ID
@router.message(AdminStates.adding_master_service)
async def admin_add_master_service_handler(message: types.Message, state: FSMContext):
    if not is_admin(message):
        return

    try:
        # Сохраняем услугу
        service = message.text.strip()
        await state.update_data(service=service)
        
        # Запрашиваем Telegram ID
        await message.answer("Введите Telegram ID мастера (числовой):")
        await state.set_state(AdminStates.adding_master_telegram)
    except Exception as e:
        logging.error(f"Ошибка в обработчике добавления услуги мастера: {e}")
        await message.answer("⚠ Ошибка ввода услуги")

# Добавление мастера - получение Telegram ID и создание мастера
@router.message(AdminStates.adding_master_telegram)
async def admin_add_master_telegram_handler(message: types.Message, state: FSMContext):
    if not is_admin(message):
        return

    try:
        # Преобразуем ID в число
        telegram_id = int(message.text.strip())
        data = await state.get_data()

        # Получаем информацию о пользователе через API Telegram
        user_info = await get_user_info(bot, telegram_id)
        username = user_info["username"] if user_info else None

        # Добавляем мастера в базу
        master_data = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "service": data["service"],
            "telegram_id": telegram_id,
            "username": username
        }
        
        success = db.add_master(master_data)
        
        if success:
            await message.answer("✅ Мастер успешно добавлен")
        else:
            await message.answer("⚠ Ошибка добавления мастера в базу данных")
            
        # Очищаем состояние
        await state.clear()
    except ValueError:
        await message.answer("⚠ Введите корректный числовой Telegram ID")
    except Exception as e:
        logging.error(f"Ошибка в обработчике добавления Telegram ID мастера: {e}")
        await message.answer("⚠ Ошибка добавления мастера")

# Удаление мастера - запрос ID
@router.callback_query(F.data == "admin_delete_master")
async def admin_delete_master_handler(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.message):
        return

    await callback.message.answer("Введите ID мастера для удаления:")
    await state.set_state(AdminStates.deleting_master)

# Удаление мастера - получение ID и удаление
@router.message(AdminStates.deleting_master)
async def admin_delete_master_id_handler(message: types.Message, state: FSMContext):
    if not is_admin(message):
        return

    try:
        # Преобразуем ID в число
        master_id = int(message.text.strip())
        
        # Получаем мастера по ID
        master = db.get_master_by_id(master_id)
        if not master:
            await message.answer("⚠️ Мастер с таким ID не найден")
            return

        # Удаляем мастера
        success = db.delete_master(master_id)
        
        if success:
            await message.answer(f"✅ Мастер {master[1]} {master[2]} успешно удален")
        else:
            await message.answer("⚠️ Ошибка удаления мастера из базы данных")
            
        # Очищаем состояние
        await state.clear()
    except ValueError:
        await message.answer("⚠️ Введите корректный ID мастера (число)")
    except Exception as e:
        logging.error(f"Ошибка в обработчике удаления мастера: {e}")
        await message.answer("⚠️ Ошибка удаления мастера")

# Просмотр отзывов
@router.callback_query(F.data == "admin_reviews")
async def admin_reviews_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Получаем все отзывы
        reviews, error = review_service.get_all_reviews()
        
        if error:
            await callback.answer(f"⚠️ {error}")
            return
            
        if not reviews:
            await callback.answer("📭 Нет отзывов")
            return

        # Отображаем список отзывов
        await callback.message.edit_text(
            "📝 Список отзывов:",
            reply_markup=get_admin_reviews_kb(reviews)
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра отзывов: {e}")
        await callback.answer("⚠️ Ошибка загрузки отзывов")

# Просмотр деталей отзыва
@router.callback_query(F.data.startswith("admin_review_"))
async def admin_review_detail_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Извлекаем ID отзыва
        review_id = callback.data.split("_")[2]
        review = db.get_review_by_id(review_id)

        if not review:
            await callback.answer("⚠️ Отзыв не найден")
            return

        # Формируем текст с деталями отзыва
        text = (
            f"⭐ Рейтинг: {review[1]}\n"
            f"💬 Комментарий: {review[2]}\n"
            f"💅 Услуга: {review[3]}\n"
            f"👤 User ID: {review[4]}\n"
            f"📅 Дата: {review[5]}"
        )

        # Отображаем с кнопками управления
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_review_detail_kb(review_id)
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра деталей отзыва: {e}")
        await callback.answer("⚠️ Ошибка загрузки отзыва")

# Блокировка отзыва
@router.callback_query(F.data.startswith("admin_block_"))
async def admin_block_review_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Извлекаем ID отзыва
        review_id = callback.data.split("_")[2]
        
        # Блокируем отзыв
        success, error = review_service.block_review(review_id)
        
        if success:
            await callback.answer("✅ Отзыв заблокирован")
            # Возвращаемся к списку отзывов
            await admin_reviews_handler(callback)
        else:
            await callback.answer(f"⚠️ {error}")
    except Exception as e:
        logging.error(f"Ошибка в обработчике блокировки отзыва: {e}")
        await callback.answer("⚠️ Ошибка блокировки отзыва")

# Возврат в главное меню админа
@router.callback_query(F.data == "admin_back")
async def admin_back_handler(callback: types.CallbackQuery):
    if not is_admin(callback.message):
        return

    try:
        # Возвращаем в главное меню
        await callback.message.edit_text(
            "🔐 Админ-панель\n"
            "Выберите действие:",
            reply_markup=get_admin_main_kb()
        )
    except Exception as e:
        logging.error(f"Ошибка в обработчике возврата в меню админа: {e}")
        await callback.answer("⚠️ Ошибка возврата в админ-панель")
