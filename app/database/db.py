import sqlite3
import logging
from app.config import DATABASE_NAME

class Database:
    def __init__(self):
        self.conn = None
        self.create_connections()
        self.create_tables()

    def create_connections(self):
        try:
            self.conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logging.info("Подключились к базе данных")
        except sqlite3.Error as e:
            logging.error(f"Ошибка подключения к базе: {e}")

    def create_tables(self):
        try:
            with self.conn:
                # Таблица записей
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS appointments(
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        service TEXT,
                        date TEXT,
                        time TEXT,
                        unique_id TEXT UNIQUE,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        master_id INTEGER
                    )''')

                # Таблица отзывов
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS reviews(
                        id INTEGER PRIMARY KEY,
                        appointment_id TEXT,
                        user_id INTEGER,
                        rating INTEGER,
                        comment TEXT,
                        status TEXT DEFAULT 'active',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )''')

                # Таблица мастеров
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS masters(
                        id INTEGER PRIMARY KEY,
                        first_name TEXT,
                        last_name TEXT,
                        service TEXT,
                        telegram_id INTEGER UNIQUE,
                        username TEXT
                    )''')
            
            logging.info("Таблицы созданы или уже существуют")
        except sqlite3.Error as e:
            logging.error(f"Ошибка создания таблиц: {e}")

    # Методы для записей
    def create_appointment(self, data):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO appointments 
                    (user_id, service, date, time, unique_id, master_id, status) 
                    VALUES (?, ?, ?, ?, ?, ?, 'active')
                ''', (data['user_id'], data['service'], data['date'], 
                      data['time'], data['unique_id'], data['master_id']))
            return True
        except Exception as e:
            logging.error(f"Ошибка создания записи: {e}")
            return False

    def get_booked_times(self, date, service):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT time FROM appointments 
                    WHERE date = ? AND service = ? AND status = 'active'
                ''', (date, service))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения занятого времени: {e}")
            return []

    def get_appointments_by_service(self, service):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT unique_id, user_id, service, date, time, master_id
                    FROM appointments 
                    WHERE service = ? AND status = 'active'
                    ORDER BY date, time
                ''', (service,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения записей по услуге: {e}")
            return []

    def get_appointment_by_id(self, unique_id):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT * FROM appointments 
                    WHERE unique_id = ?
                ''', (unique_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка получения записи: {e}")
            return None

    def cancel_appointment(self, unique_id):
        try:
            with self.conn:
                self.conn.execute('''
                    UPDATE appointments 
                    SET status = 'canceled' 
                    WHERE unique_id = ?
                ''', (unique_id,))
            return True
        except Exception as e:
            logging.error(f"Ошибка отмены записи: {e}")
            return False

    # Методы для отзывов
    def add_review(self, data):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO reviews 
                    (appointment_id, user_id, rating, comment)
                    VALUES (?, ?, ?, ?)
                ''', (data['unique_id'], data['user_id'],
                    data['rating'], data['comment']))
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления отзыва: {e}")
            return False

    def get_user_reviews(self, user_id):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT r.rating, r.comment, a.service, a.date 
                    FROM reviews r
                    JOIN appointments a ON r.appointment_id = a.unique_id
                    WHERE r.user_id = ? AND r.status = 'active'
                ''', (user_id,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения отзывов пользователя: {e}")
            return []

    def get_all_reviews(self):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT r.id, r.rating, r.comment, a.service, r.user_id
                    FROM reviews r
                    JOIN appointments a ON r.appointment_id = a.unique_id
                    WHERE r.status = 'active'
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения всех отзывов: {e}")
            return []
            
    def get_review_by_id(self, review_id):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT r.id, r.rating, r.comment, a.service, r.user_id, r.created_at
                    FROM reviews r
                    JOIN appointments a ON r.appointment_id = a.unique_id
                    WHERE r.id = ?
                ''', (review_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка получения отзыва: {e}")
            return None

    def block_review(self, review_id):
        try:
            with self.conn:
                self.conn.execute('''
                    UPDATE reviews 
                    SET status = 'blocked' 
                    WHERE id = ?
                ''', (review_id,))
            return True
        except Exception as e:
            logging.error(f"Ошибка блокировки отзыва: {e}")
            return False

    # Методы для мастеров
    def add_master(self, data):
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO masters 
                    (first_name, last_name, service, telegram_id, username)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data['first_name'], data['last_name'],
                    data['service'], data['telegram_id'], data['username']))
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления мастера: {e}")
            return False

    def get_masters_by_service(self, service):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT id, first_name, last_name 
                    FROM masters 
                    WHERE service = ?
                ''', (service,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения мастеров по услуге: {e}")
            return []

    def get_master_by_id(self, master_id):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT * FROM masters 
                    WHERE id = ?
                ''', (master_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка получения мастера по ID: {e}")
            return None

    def get_master_by_telegram_id(self, telegram_id):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT * FROM masters 
                    WHERE telegram_id = ?
                ''', (telegram_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка получения мастера по Telegram ID: {e}")
            return None

    def get_all_masters(self):
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT id, first_name, last_name, service, telegram_id, username 
                    FROM masters
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения всех мастеров: {e}")
            return []

    def delete_master(self, master_id):
        try:
            with self.conn:
                self.conn.execute('''
                    DELETE FROM masters 
                    WHERE id = ?
                ''', (master_id,))
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления мастера: {e}")
            return False

    def get_today_appointments_for_master(self, master_id):
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT unique_id, user_id, service, time 
                    FROM appointments 
                    WHERE date = ? AND master_id = ? AND status = 'active'
                    ORDER BY time
                ''', (today, master_id))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения сегодняшних записей мастера: {e}")
            return []

    def get_upcoming_appointments_for_master(self, master_id):
        try:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            with self.conn:
                cursor = self.conn.execute('''
                    SELECT unique_id, date, time, service, user_id 
                    FROM appointments 
                    WHERE date >= ? AND master_id = ? AND status = 'active'
                    ORDER BY date, time
                ''', (today, master_id))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения предстоящих записей мастера: {e}")
            return []
