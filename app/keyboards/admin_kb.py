from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import SERVICES

def get_admin_main_kb():
    """Основная клавиатура админа"""
    builder = InlineKeyboardBuilder()
    for service, emoji in SERVICES.items():
        builder.button(text=f"{emoji} {service}", callback_data=f"admin_service_{service}")
    
    builder.button(text="👨‍🔧 Управление мастерами", callback_data="admin_masters")
    builder.button(text="📝 Отзывы", callback_data="admin_reviews")
    builder.adjust(2)
    return builder.as_markup()

def get_admin_masters_kb():
    """Клавиатура управления мастерами"""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить мастера", callback_data="admin_add_master")
    builder.button(text="➖ Удалить мастера", callback_data="admin_delete_master")
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_reviews_kb(reviews):
    """Клавиатура с отзывами для админа"""
    builder = InlineKeyboardBuilder()
    for review in reviews:
        builder.button(
            text=f"⭐ {review[1]} от пользователя {review[4]}",
            callback_data=f"admin_review_{review[0]}"
        )
    builder.button(text="🔙 Назад", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_review_detail_kb(review_id):
    """Клавиатура деталей отзыва"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Заблокировать", callback_data=f"admin_block_{review_id}")
    builder.button(text="🔙 Назад", callback_data="admin_reviews")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_back_kb():
    """Клавиатура с кнопкой Назад"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="admin_back")
    return builder.as_markup()
