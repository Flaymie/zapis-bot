import logging
from aiogram import Bot

async def get_user_info(bot: Bot, user_id: int):
    """Получение информации о пользователе через API Telegram"""
    try:
        user = await bot.get_chat(user_id)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username
        }
    except Exception as e:
        logging.error(f"Ошибка получения информации о пользователе: {e}")
        return None

def format_master_info(master):
    """Форматирование информации о мастере"""
    if not master:
        return "Мастер не найден"
        
    username = f" (@{master[5]})" if master[5] else ""
    return f"{master[1]} {master[2]}{username}"

def format_appointment_info(appointment, with_id=True):
    """Форматирование информации о записи"""
    if not appointment:
        return "Запись не найдена"
        
    text = ""
    if with_id:
        text += f"🔑 ID: {appointment['unique_id']}\n"
        
    text += (
        f"💅 Услуга: {appointment['service']}\n"
        f"📅 Дата: {appointment['date']}\n"
        f"⏰ Время: {appointment['time']}\n"
    )
    
    if 'user_id' in appointment:
        text += f"👤 User ID: {appointment['user_id']}\n"
        
    return text
