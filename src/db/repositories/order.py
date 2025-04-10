import asyncpg
import structlog

from src.db.db_api.storages import PostgresConnection
from src.models.order import OrderModel


class OrderRepository(PostgresConnection):
    def __init__(
        self,
        connection_poll: asyncpg.Pool,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        super().__init__(connection_poll, logger)

    async def get_order_by_uuid(self, uuid: str) -> OrderModel | None:
        """
        Fetch an order by its UUID.
        """
        statement = """
        SELECT id, uuid, is_paid, user_id, amount
        FROM public."order"
        WHERE uuid = $1;
        """
        result = await self._fetchrow(sql=statement, params=(uuid,))
        if not result:
            return None
        return result.convert(OrderModel)

    async def create_order(self, uuid: str, user_id: int, amount: float) -> int:
        """
        Create a new order in the database.
        """
        statement = """
        INSERT INTO public."order" (uuid, user_id, amount)
        VALUES ($1, $2, $3)
        RETURNING id;
        """
        result = await self._execute(sql=statement, params=(uuid, user_id, amount))
        return result

    async def update_order_is_paid(self, uuid: str, is_paid: bool) -> None:
        """
        Update the `is_paid` field of an order by its UUID.
        """
        statement = """
        UPDATE public."order"
        SET is_paid = $1
        WHERE uuid = $2;
        """
        await self._execute(sql=statement, params=(is_paid, uuid))
