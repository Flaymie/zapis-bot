import logging

class ReviewService:
    def __init__(self, db):
        self.db = db
        
    def add_review(self, unique_id, user_id, rating, comment):
        """Добавление отзыва"""
        try:
            # Получаем запись по уникальному ID
            appointment = self.db.get_appointment_by_id(unique_id)
            if not appointment:
                return False, "Запись не найдена"
                
            # Проверяем, принадлежит ли запись пользователю
            if appointment[1] != user_id:
                return False, "Вы не можете оставить отзыв на чужую запись"
                
            # Добавляем отзыв
            success = self.db.add_review({
                'unique_id': unique_id,
                'user_id': user_id,
                'rating': rating,
                'comment': comment
            })
            
            if not success:
                return False, "Ошибка сохранения отзыва"
                
            return True, None
        except Exception as e:
            logging.error(f"Ошибка добавления отзыва: {e}")
            return False, f"Ошибка при добавлении отзыва: {str(e)}"
            
    def get_user_reviews(self, user_id):
        """Получение отзывов пользователя"""
        try:
            return self.db.get_user_reviews(user_id), None
        except Exception as e:
            logging.error(f"Ошибка получения отзывов пользователя: {e}")
            return None, f"Ошибка при получении отзывов: {str(e)}"
            
    def get_all_reviews(self):
        """Получение всех отзывов"""
        try:
            return self.db.get_all_reviews(), None
        except Exception as e:
            logging.error(f"Ошибка получения всех отзывов: {e}")
            return None, f"Ошибка при получении отзывов: {str(e)}"
            
    def block_review(self, review_id):
        """Блокировка отзыва админом"""
        try:
            success = self.db.block_review(review_id)
            if not success:
                return False, "Ошибка блокировки отзыва"
                
            return True, None
        except Exception as e:
            logging.error(f"Ошибка блокировки отзыва: {e}")
            return False, f"Ошибка при блокировке отзыва: {str(e)}"
