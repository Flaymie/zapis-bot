import logging
import uuid
from datetime import datetime, timedelta

class AppointmentService:
    def __init__(self, db, notification_service):
        self.db = db
        self.notification_service = notification_service

    def generate_dates(self):
        """Генерация дат на месяц вперед"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return [today + timedelta(days=i) for i in range(1, 31)]

    def generate_times(self):
        """Генерация доступного времени"""
        return [f"{hour:02d}:00" for hour in range(11, 23)]

    def create_appointment(self, user_id, service, date, time, master_id):
        """Создание записи в базе"""
        try:
            # Генерация уникального ID записи
            unique_id = str(uuid.uuid4())[:8].upper()
            
            # Проверяем, свободно ли выбранное время
            booked_times = self.db.get_booked_times(date, service)
            if time in booked_times:
                return None, "Выбранное время уже занято"
            
            # Создаем словарь с данными записи
            appointment_data = {
                'user_id': user_id,
                'service': service,
                'date': date,
                'time': time,
                'unique_id': unique_id,
                'master_id': master_id
            }
            
            # Создаем запись в базе
            success = self.db.create_appointment(appointment_data)
            if not success:
                return None, "Ошибка создания записи в базе"
                
            return appointment_data, None
        except Exception as e:
            logging.error(f"Ошибка создания записи: {e}")
            return None, f"Ошибка при создании записи: {str(e)}"
    
    async def process_appointment(self, user_id, appointment_data):
        """Обработка новой записи и отправка уведомлений"""
        try:
            # Отправляем уведомление администратору
            await self.notification_service.send_admin_notification(appointment_data)
            
            # Отправляем уведомление мастеру
            await self.notification_service.send_master_notification(
                appointment_data['master_id'], 
                appointment_data
            )
            
            # Планируем напоминания
            self.notification_service.schedule_notifications(user_id, appointment_data)
            
            return True
        except Exception as e:
            logging.error(f"Ошибка обработки записи: {e}")
            return False
            
    async def cancel_appointment(self, unique_id, user_id, is_admin=False):
        """Отмена записи"""
        try:
            # Получаем информацию о записи
            appointment = self.db.get_appointment_by_id(unique_id)
            if not appointment:
                return False, "Запись не найдена"
                
            # Проверяем права на отмену
            if appointment[1] != user_id and not is_admin:
                return False, "У вас нет прав на отмену этой записи"
                
            # Проверяем статус записи
            if appointment[6] != 'active':
                return False, "Запись уже отменена"
                
            # Отменяем запись
            success = self.db.cancel_appointment(unique_id)
            if not success:
                return False, "Ошибка отмены записи"
                
            # Отправляем уведомление об отмене администратору
            await self.notification_service.send_admin_notification({
                'unique_id': unique_id,
                'status': 'canceled',
                'service': appointment[2],
                'date': appointment[3],
                'time': appointment[4],
                'user_id': appointment[1],
                'master_id': appointment[8] if len(appointment) > 8 else None
            })
            
            # Если запись отменена администратором, отправляем уведомление пользователю
            if is_admin and appointment[1] != user_id:
                await self.notification_service.send_cancellation_notification(
                    appointment[1],
                    {
                        'unique_id': appointment[5],
                        'service': appointment[2],
                        'date': appointment[3],
                        'time': appointment[4]
                    }
                )
                
            return True, None
        except Exception as e:
            logging.error(f"Ошибка отмены записи: {e}")
            return False, f"Ошибка при отмене записи: {str(e)}"
