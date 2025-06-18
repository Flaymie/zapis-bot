from aiogram.fsm.state import StatesGroup, State

# Состояния для процесса записи клиента
class BookingStates(StatesGroup):
    choosing_service = State()
    choosing_date = State()
    choosing_time = State()
    confirmation = State()
    review_rating = State()
    review_comment = State()
    choosing_master = State()
    cancel_appointment = State()

# Состояния для функций администратора
class AdminStates(StatesGroup):
    adding_master_name = State()
    adding_master_service = State()
    adding_master_telegram = State()
    deleting_master = State()
