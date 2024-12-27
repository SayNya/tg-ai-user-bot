from aiogram.fsm.state import State, StatesGroup


class UserMainMenu(StatesGroup):
    menu = State()


class UserTheme(StatesGroup):
    name = State()
    description = State()
