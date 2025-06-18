import logging
from datetime import datetime, timedelta
from app.config import ADMIN_ID
from app.keyboards.user_kb import get_rating_kb

class NotificationService:
    def __init__(self, bot, db, scheduler):
        self.bot = bot
        self.db = db
        self.scheduler = scheduler

    async def send_admin_notification(self, appointment):
        """Отправка уведомления админу о новой/отмененной записи"""
        try:
            master = self.db.get_master_by_id(appointment.get('master_id'))
            if not master and 'master_id' in appointment:
                logging.error(f"Мастер с ID {appointment['master_id']} не найден")
                return
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления администратору: {e}")
            return

        if 'status' in appointment and appointment['status'] == 'canceled':
            text = (
                "🚫 Запись отменена!\n"
                f"🔑 ID: {appointment['unique_id']}\n"
                f"💅 Услуга: {appointment['service']}\n"
                f"📅 Дата: {appointment['date']}\n"
                f"⏰ Время: {appointment['time']}\n"
                f"👤 User ID: {appointment['user_id']}"
            )
        else:
            if master:
                username = f" (@{master[5]})" if master[5] else ""
                master_info = f"👨‍🔧 Мастер: {master[1]} {master[2]}{username}\n"
            else:
                master_info = ""
                
            text = (
                "📌 Новая запись!\n"
                f"🔑 ID: {appointment['unique_id']}\n"
                f"💅 Услуга: {appointment['service']}\n"
                f"{master_info}"
                f"📅 Дата: {appointment['date']}\n"
                f"⏰ Время: {appointment['time']}\n"
                f"👤 User ID: {appointment['user_id']}"
            )
            
        await self.bot.send_message(ADMIN_ID, text)

    async def send_master_notification(self, master_id, appointment):
        """Отправка уведомления мастеру о новой записи"""
        master = self.db.get_master_by_id(master_id)
        if not master or not master[4]:  # Проверяем, есть ли мастер и его Telegram ID
            return

        try:
            await self.bot.send_message(
                master[4],
                f"📌 У вас новая запись!\n"
                f"💅 Услуга: {appointment['service']}\n"
                f"📅 Дата: {appointment['date']}\n"
                f"⏰ Время: {appointment['time']}"
            )
        except Exception as e:
            logging.error(f"Ошибка отправки уведомления мастеру: {e}")

    async def send_reminder(self, user_id, appointment):
        """Отправка напоминания о записи"""
        text = (
            "🔔 Напоминание о записи!\n"
            f"💅 Услуга: {appointment['service']}\n"
            f"📅 Дата: {appointment['date']}\n"
            f"⏰ Время: {appointment['time']}"
        )
        await self.bot.send_message(user_id, text)

    async def request_review(self, user_id, unique_id):
        """Запрос отзыва после посещения"""
        keyboard = get_rating_kb(unique_id)
        await self.bot.send_message(
            user_id,
            "Пожалуйста, оцените наше обслуживание:",
            reply_markup=keyboard
        )

    async def send_cancellation_notification(self, user_id, appointment):
        """Уведомление пользователя об отмене записи администратором"""
        text = (
            "🚫 Ваша запись была отменена администратором.\n"
            f"🔑 ID записи: {appointment['unique_id']}\n"
            f"💅 Услуга: {appointment['service']}\n"
            f"📅 Дата: {appointment['date']}\n"
            f"⏰ Время: {appointment['time']}"
        )
        await self.bot.send_message(user_id, text)
        
    def schedule_notifications(self, user_id, appointment_data):
        """Планирование отправки напоминаний и запроса отзыва"""
        try:
            # Преобразуем строковую дату и время в объект datetime
            appointment_datetime = datetime.strptime(
                f"{appointment_data['date']} {appointment_data['time']}", 
                "%Y-%m-%d %H:%M"
            )

            # Напоминание за день до записи
            self.scheduler.add_job(
                self.send_reminder,
                'date',
                run_date=appointment_datetime - timedelta(days=1),
                args=[user_id, appointment_data]
            )

            # Напоминание за 2 часа до записи
            self.scheduler.add_job(
                self.send_reminder,
                'date',
                run_date=appointment_datetime - timedelta(hours=2),
                args=[user_id, appointment_data]
            )

            # Запрос отзыва через 2 часа после записи
            self.scheduler.add_job(
                self.request_review,
                'date',
                run_date=appointment_datetime + timedelta(hours=2),
                args=[user_id, appointment_data['unique_id']]
            )
            
            logging.info(f"Запланированы уведомления для записи {appointment_data['unique_id']}")
        except Exception as e:
            logging.error(f"Ошибка планирования уведомлений: {e}")
