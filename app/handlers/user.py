import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from app.models.states import BookingStates
from app.keyboards.user_kb import (
    get_services_kb, 
    get_masters_kb, 
    get_dates_kb, 
    get_times_kb, 
    get_confirmation_kb
)
from app.services.appointment import AppointmentService
from app.services.review import ReviewService
from app.utils.helpers import format_master_info

# Создаем роутер для пользовательских команд
router = Router()

# Инициализируем сервисы (они будут переданы при регистрации роутера)
appointment_service = None
review_service = None
db = None

def init_services(appointment_svc, review_svc, database):
    """Функция для инициализации сервисов при старте бота"""
    global appointment_service, review_service, db
    appointment_service = appointment_svc
    review_service = review_svc
    db = database

# Команда старт - начало записи
@router.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    try:
        await message.answer(
            "✨ Добро пожаловать в салон красоты!\n"
            "Выберите услугу:",
            reply_markup=get_services_kb()
        )
        await state.set_state(BookingStates.choosing_service)
    except Exception as e:
        logging.error(f"Ошибка в обработчике start: {e}")
        await message.answer("⚠ Произошла ошибка. Пожалуйста, попробуйте позже.")

# Выбор услуги
@router.callback_query(F.data.startswith("service_"), BookingStates.choosing_service)
async def service_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Извлекаем название услуги из callback_data
        service = callback.data.split("_")[1]
        await state.update_data(service=service)

        # Получаем список мастеров для выбранной услуги
        masters = db.get_masters_by_service(service)
        if not masters:
            await callback.message.answer("⚠ Нет доступных мастеров для этой услуги")
            return

        # Отображаем список мастеров
        await callback.message.edit_text(
            "👨‍🔧 Выберите мастера:",
            reply_markup=get_masters_kb(masters)
        )
        await state.set_state(BookingStates.choosing_master)
    except Exception as e:
        logging.error(f"Ошибка в обработчике выбора услуги: {e}")
        await callback.message.answer("⚠ Ошибка выбора услуги")

# Выбор мастера
@router.callback_query(F.data.startswith("master_"), BookingStates.choosing_master)
async def master_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Извлекаем ID мастера из callback_data
        master_id = int(callback.data.split("_")[1])
        master = db.get_master_by_id(master_id)
        
        if not master:
            await callback.answer("⚠️ Мастер не найден")
            return

        # Сохраняем информацию о мастере
        await state.update_data(master_id=master_id)
        master_name = format_master_info(master)
        await state.update_data(master_name=master_name)

        # Отображаем доступные даты
        await callback.message.edit_text(
            f"👨‍🔧 Мастер: {master_name}\n"
            "📅 Выберите дату записи:",
            reply_markup=get_dates_kb()
        )
        await state.set_state(BookingStates.choosing_date)
    except ValueError:
        await callback.answer("⚠️ Ошибка: неверный ID мастера")
    except Exception as e:
        logging.error(f"Ошибка в обработчике выбора мастера: {e}")
        await callback.answer("⚠️ Ошибка выбора мастера")

# Выбор даты
@router.callback_query(F.data.startswith("date_"), BookingStates.choosing_date)
async def date_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Извлекаем выбранную дату
        selected_date = callback.data.split("_")[1]
        data = await state.get_data()

        if 'service' not in data:
            await callback.answer("⚠ Сначала выберите услугу!")
            return

        # Получаем уже забронированное время
        booked_times = db.get_booked_times(selected_date, data['service'])
        
        # Сохраняем выбранную дату
        await state.update_data(date=selected_date)
        
        # Отображаем доступное время
        await callback.message.edit_text(
            f"⏰ Выберите время для {selected_date}:",
            reply_markup=get_times_kb(selected_date, booked_times)
        )
        await state.set_state(BookingStates.choosing_time)
    except Exception as e:
        logging.error(f"Ошибка в обработчике выбора даты: {e}")
        await callback.message.answer("⚠ Ошибка выбора даты, начните заново /start")

# Выбор времени
@router.callback_query(F.data.startswith("time_"), BookingStates.choosing_time)
async def time_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Проверяем, не заблокировано ли время
        if callback.data == "time_blocked":
            await callback.answer("⚠️ Это время уже занято!")
            return
            
        # Извлекаем выбранное время
        selected_time = callback.data.split("_")[1]
        await state.update_data(time=selected_time)
        data = await state.get_data()

        # Формируем текст подтверждения
        text = (
            "✅ Подтвердите запись:\n"
            f"💅 Услуга: {data['service']}\n"
            f"👨‍🔧 Мастер: {data['master_name']}\n"
            f"📅 Дата: {data['date']}\n"
            f"⏰ Время: {data['time']}"
        )

        # Отображаем подтверждение
        await callback.message.edit_text(
            text, 
            reply_markup=get_confirmation_kb()
        )
        await state.set_state(BookingStates.confirmation)
    except Exception as e:
        logging.error(f"Ошибка в обработчике выбора времени: {e}")
        await callback.message.answer("⚠️ Ошибка выбора времени")

# Подтверждение записи
@router.callback_query(F.data == "confirm_yes", BookingStates.confirmation)
async def confirm_yes_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Получаем все сохраненные данные
        data = await state.get_data()
        
        # Создаем запись
        appointment_data, error = appointment_service.create_appointment(
            callback.from_user.id,
            data['service'],
            data['date'],
            data['time'],
            data['master_id']
        )
        
        if error:
            await callback.message.answer(f"⚠️ {error}")
            return
            
        # Обрабатываем запись (отправляем уведомления и т.д.)
        success = await appointment_service.process_appointment(
            callback.from_user.id,
            appointment_data
        )
        
        if success:
            await callback.message.edit_text(
                f"✅ Запись успешно создана!\n"
                f"Ваш ID: {appointment_data['unique_id']}"
            )
        else:
            await callback.message.edit_text(
                f"✅ Запись создана, но возникли проблемы с отправкой уведомлений.\n"
                f"Ваш ID: {appointment_data['unique_id']}"
            )
            
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при подтверждении записи: {e}")
        await callback.message.answer("⚠️ Ошибка создания записи")

# Отмена при подтверждении
@router.callback_query(F.data == "confirm_no", BookingStates.confirmation)
async def confirm_no_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Запись отменена")
    await state.clear()

# Команда отмены записи
@router.message(Command("cancel"))
async def cancel_command_handler(message: types.Message, state: FSMContext):
    await message.answer("❓ Введите ID записи для отмены:")
    await state.set_state(BookingStates.cancel_appointment)

# Обработка ID для отмены записи
@router.message(BookingStates.cancel_appointment)
async def cancel_appointment_handler(message: types.Message, state: FSMContext):
    try:
        # Получаем ID записи
        unique_id = message.text.strip().upper()
        
        # Отменяем запись
        success, error = await appointment_service.cancel_appointment(
            unique_id, 
            message.from_user.id
        )
        
        if success:
            await message.answer(f"✅ Запись {unique_id} успешно отменена")
        else:
            await message.answer(f"⚠️ {error}")
            
        # Очищаем состояние
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка при отмене записи: {e}")
        await message.answer("⚠️ Ошибка отмены записи. Пожалуйста, попробуйте позже.")

# Обработка запроса отзыва
@router.callback_query(F.data.startswith("review_"))
async def review_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Разбираем данные из callback
        parts = callback.data.split("_")
        if len(parts) != 3:
            await callback.answer("⚠️ Неверный формат данных")
            return
            
        unique_id, rating = parts[1], parts[2]
        
        # Проверяем существование записи
        appointment = db.get_appointment_by_id(unique_id)
        if not appointment:
            await callback.answer("⚠️ Запись не найдена!")
            return

        # Сохраняем данные отзыва
        await state.update_data(
            review_unique_id=unique_id,
            review_rating=rating
        )
        
        # Запрашиваем комментарий
        await callback.message.answer(
            "💬 Напишите комментарий (или отправьте '-' чтобы пропустить):"
        )
        await state.set_state(BookingStates.review_comment)
    except Exception as e:
        logging.error(f"Ошибка в обработчике отзыва: {e}")
        await callback.answer("⚠️ Ошибка обработки отзыва")

# Обработка комментария к отзыву
@router.message(BookingStates.review_comment)
async def review_comment_handler(message: types.Message, state: FSMContext):
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        comment = message.text if message.text != "-" else ""

        # Добавляем отзыв
        success, error = review_service.add_review(
            data['review_unique_id'],
            message.from_user.id,
            data['review_rating'],
            comment
        )
        
        if success:
            await message.answer("💖 Спасибо за ваш отзыв!")
        else:
            await message.answer(f"⚠️ {error}")

        # Очищаем состояние
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка в обработчике комментария: {e}")
        await message.answer("⚠ Ошибка обработки комментария")

# Просмотр отзывов пользователем
@router.message(Command("reviews"))
async def user_reviews_handler(message: types.Message):
    try:
        # Получаем отзывы пользователя
        reviews, error = review_service.get_user_reviews(message.from_user.id)
        
        if error:
            await message.answer(f"⚠️ {error}")
            return
            
        if not reviews:
            await message.answer("📭 У вас пока нет отзывов")
            return

        # Формируем текст с отзывами
        text = "⭐ Ваши отзывы:\n\n"
        for review in reviews:
            text += (
                f"💅 Услуга: {review[2]}\n"
                f"📅 Дата: {review[3]}\n"
                f"Рейтинг: {review[0]}⭐\n"
                f"💬 Комментарий: {review[1]}\n"
                "━━━━━━━━━━━━━━\n"
            )

        await message.answer(text)
    except Exception as e:
        logging.error(f"Ошибка в обработчике просмотра отзывов: {e}")
        await message.answer("⚠️ Ошибка загрузки отзывов")
