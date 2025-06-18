from aiogram import Dispatcher

from app.handlers.user import router as user_router, init_services as init_user_services
from app.handlers.admin import router as admin_router, init_services as init_admin_services
from app.handlers.master import router as master_router, init_services as init_master_services

from app.services.appointment import AppointmentService
from app.services.review import ReviewService
from app.services.notification import NotificationService
from app.database.db import Database

def register_handlers(dp: Dispatcher, bot, scheduler):
    """Регистрирует все обработчики и инициализирует сервисы"""
    
    # Инициализация базы данных и сервисов
    db = Database()
    notification_service = NotificationService(bot, db, scheduler)
    appointment_service = AppointmentService(db, notification_service)
    review_service = ReviewService(db)
    
    # Инициализация сервисов для обработчиков
    init_user_services(appointment_service, review_service, db)
    init_admin_services(appointment_service, review_service, db, bot)
    init_master_services(db)
    
    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(master_router)
    
    return db  # Возвращаем экземпляр базы данных для использования в других местах
