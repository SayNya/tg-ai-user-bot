from aiogram.fsm.state import State, StatesGroup


class UserMainMenu(StatesGroup):
    menu = State()


class UserTheme(StatesGroup):
    name = State()
    description = State()
    gpt = State()


class UserRegistration(StatesGroup):
    phone = State()
    api_id = State()
    api_hash = State()
    have_password = State()
    password = State()
    tg_code = State()
