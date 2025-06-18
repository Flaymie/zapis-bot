from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from datetime import datetime, timedelta
from app.config import SERVICES

def get_services_kb():
    """Клавиатура для выбора услуги"""
    builder = InlineKeyboardBuilder()
    for service, emoji in SERVICES.items():
        builder.button(text=f"{emoji} {service}", callback_data=f"service_{service}")
    builder.adjust(2)
    return builder.as_markup()

def get_masters_kb(masters):
    """Клавиатура для выбора мастера"""
    builder = InlineKeyboardBuilder()
    for master in masters:
        builder.button(
            text=f"{master[1]} {master[2]}",
            callback_data=f"master_{master[0]}"
        )
    builder.adjust(1)
    return builder.as_markup()

def get_dates_kb():
    """Клавиатура с датами на месяц вперёд"""
    # Генерируем даты на месяц вперед
    dates = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(1, 31):
        dates.append(today + timedelta(days=i))

    builder = InlineKeyboardBuilder()
    for date in dates:
        builder.add(InlineKeyboardButton(
            text=date.strftime("%d.%m.%Y"),
            callback_data=f"date_{date.strftime('%Y-%m-%d')}"
        ))
    builder.adjust(3)
    return builder.as_markup()

def get_times_kb(selected_date, booked_times):
    """Клавиатура с доступным временем"""
    builder = InlineKeyboardBuilder()
    all_times = [f"{hour:02d}:00" for hour in range(11, 23)]
    
    for time in all_times:
        if time in booked_times:
            builder.button(text=f"❌ {time}", callback_data="time_blocked")
        else:
            builder.button(text=time, callback_data=f"time_{time}")
    
    builder.adjust(4)
    return builder.as_markup()

def get_confirmation_kb():
    """Клавиатура подтверждения записи"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_yes")
    builder.button(text="❌ Отменить", callback_data="confirm_no")
    return builder.as_markup()

def get_rating_kb(unique_id):
    """Клавиатура для оценки"""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.button(text=f"{i}⭐", callback_data=f"review_{unique_id}_{i}")
    builder.adjust(5)
    return builder.as_markup()
