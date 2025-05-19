from sqlalchemy import select

from .session import async_session_factory
from .tables import Chat


async def get_user_chat_tg_ids_from_db(user_id: int) -> list[int]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(Chat.telegram_chat_id).where(Chat.user_id == user_id),
        )
        return result.scalars().all()
