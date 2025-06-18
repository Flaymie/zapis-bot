import os
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация бота
BOT_TOKEN = os.getenv('BOT_TOKEN', '7300868368:AAG5so8v4nh8QojFobdOL7VhmEm_YLP6Wus')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5170509558'))
DATABASE_NAME = os.getenv('DATABASE_NAME', 'salon.db')

# Список доступных услуг с emoji
SERVICES = {
    "Маникюр": "💅",
    "Педикюр": "👠",
    "Стрижка": "✂️",
    "Покраска": "🎨"
}
