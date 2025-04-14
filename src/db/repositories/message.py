import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models import MessageModel


class MessageRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def create_message(
        self,
        msg_id: int,
        text: str,
        chat_id: int,
        user_id: int,
        sender_id: int,
        theme_id: int,
        sender_username: str | None = None,
        mentioned_id: int | None = None,
    ) -> None:
        statement = "INSERT INTO message (id, text, mentioned_id, chat_id, user_id, sender_id, theme_id, sender_username) VALUES ($1, $2, $3, $4, $5, $6, $7, $8);"
        await self._execute(
            sql=statement,
            params=(
                msg_id,
                text,
                mentioned_id,
                chat_id,
                user_id,
                sender_id,
                theme_id,
                sender_username,
            ),
        )

    async def get_mentioned_message(
        self,
        msg_id: int,
        chat_id: int,
        sender_id: int,
        user_id: int,
    ) -> MessageModel | None:
        statement = "SELECT id, text, mentioned_id, chat_id, user_id, sender_id, created_at, theme_id FROM message WHERE id = $1 AND chat_id = $2 AND user_id = $3 AND sender_id = $4;"

        result = await self._fetchrow(
            sql=statement,
            params=(msg_id, chat_id, user_id, sender_id),
        )
        return result.convert(MessageModel)

    async def get_messages_tree(
        self,
        message_id: int,
    ) -> list[MessageModel] | None:
        statement = """
            WITH RECURSIVE message_tree AS (
                SELECT m.*
                FROM message m
                WHERE m.id = $1
                
                UNION ALL
                
                SELECT parent.*
                FROM message parent
                JOIN message_tree child ON parent.id = child.mentioned_id
            )
            SELECT * FROM message_tree ORDER BY created_at;
            """
        result = await self._fetch(sql=statement, params=(message_id,))
        return result.convert(MessageModel)

    async def get_private_chat_history(
        self,
        chat_id: int,
        user_id: int,
    ) -> list[MessageModel] | None:
        statement = """
        SELECT id, text, mentioned_id, chat_id, user_id, sender_id, created_at, theme_id
        FROM message
        WHERE chat_id = $1 AND user_id = $2
        ORDER BY created_at;
        """

        result = await self._fetch(sql=statement, params=(chat_id, user_id))
        return result.convert(MessageModel)
