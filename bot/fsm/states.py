from aiogram.fsm.state import State, StatesGroup

class GameStates(StatesGroup):
    MAIN_MENU = State()
    CHOOSING_PLATFORM = State()
    VIEWING_ORDERS = State()
    ACCEPTING_ORDER = State()
    RIDING_TO_RESTAURANT = State()
    RIDING_TO_CLIENT = State()
    MINIGAME_TETRIS = State()
    MINIGAME_DIALOG = State()
    MINIGAME_BROKEN = State()
    MINIGAME_BOOKING = State()
    GARAGE_MAIN = State()
    GARAGE_SERVICE = State()
    GARAGE_TUNING = State()
    GARAGE_SHOP = State()
    PATROL_ENCOUNTER = State()