from aiogram import types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import User
from src.models.user import UserCreate


async def start(
    msg: types.Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.clear()

    tg_user = msg.from_user

    result = await session.scalars(
        select(User).where(User.telegram_user_id == tg_user.id),
    )
    db_user = result.first()

    if not db_user:
        new_user = UserCreate(
            telegram_user_id=tg_user.id,
            username=tg_user.username,
            is_bot=tg_user.is_bot,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
        )

        user = User(**new_user.model_dump())
        session.add(user)
        await session.commit()
