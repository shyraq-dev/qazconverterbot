from aiogram.fsm.state import State, StatesGroup


class ConvertState(StatesGroup):
    waiting_format = State()        # Жалғыз сурет — формат күту
    collecting_photos = State()     # Альбом жинау
    waiting_multi_format = State()  # Көп сурет — формат күту
