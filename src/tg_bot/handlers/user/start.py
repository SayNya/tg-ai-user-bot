import asyncpg
import structlog
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.db.repositories import UserRepository


async def start(
    msg: types.Message,
    state: FSMContext,
    db_pool: asyncpg.Pool,
    db_logger: structlog.typing.FilteringBoundLogger,
) -> None:
    if msg.from_user is None:
        return
    await state.clear()
    user_repository = UserRepository(connection_poll=db_pool, logger=db_logger)
    db_user = await user_repository.get_user_by_id(msg.from_user.id)

    if not db_user:
        await user_repository.create_user(
            user_id=msg.from_user.id,
            is_bot=msg.from_user.is_bot,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name,
            username=msg.from_user.username,
            language_code=msg.from_user.language_code,
        )
