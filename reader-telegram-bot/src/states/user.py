from aiogram.fsm.state import State, StatesGroup


class UserMainMenu(StatesGroup):
    menu = State()


class UserTopic(StatesGroup):
    name = State()
    description = State()
    gpt = State()


class UserRegistration(StatesGroup):
    phone = State()
    api_id = State()
    api_hash = State()
    tg_code = State()
    password = State()


class TopicEdit(StatesGroup):
    edit_name = State()
    edit_description = State()
    edit_prompt = State()
