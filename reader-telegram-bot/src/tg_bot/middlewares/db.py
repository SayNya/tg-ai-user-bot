from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker) -> None:
        super().__init__()
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:  # noqa: ANN401
        async with self.sessionmaker() as session:
            data["session"] = session
            return await handler(event, data)
