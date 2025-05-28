from aiogram import types
from aiogram.fsm.context import FSMContext

from src.db.repositories import UserRepository
from src.exceptions import DatabaseNotFoundError
from src.models.database import UserCreateDB


async def start(
    msg: types.Message,
    state: FSMContext,
    user_repository: UserRepository,
) -> None:
    await state.clear()

    tg_user = msg.from_user
    try:
        await user_repository.get(tg_user.id)
    except DatabaseNotFoundError:
        user_create = UserCreateDB(
            id=tg_user.id,
            is_bot=tg_user.is_bot,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
            language_code=tg_user.language_code,
        )
        await user_repository.create(user_create)
