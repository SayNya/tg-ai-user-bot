import structlog

from src.exceptions import (
    ClientNotFoundError,
    DatabaseNotFoundError,
)
from src.infrastructure import RabbitMQPublisher, TelethonClientManager
from src.models.enums.infrastructure import RabbitMQQueuePublisher


class ClientService:
    def __init__(
        self,
        client_manager: TelethonClientManager,
        publisher: RabbitMQPublisher,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.client_manager = client_manager
        self.publisher = publisher
        self.logger = logger

    async def start_client(self, user_id: int) -> None:
        self.logger.info("starting_client", user_id=user_id)
        try:
            await self.client_manager.start_client_by_telegram_user_id(user_id)
        except DatabaseNotFoundError:
            self.logger.exception("client_not_found", user_id=user_id)
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_ERROR,
                {"user_id": user_id, "error": "Client not found"},
            )
            return

        self.logger.info("client_started", user_id=user_id)
        await self.publisher.publish(
            RabbitMQQueuePublisher.CLIENT_STARTED,
            {"user_id": user_id},
        )

    async def stop_client(self, user_id: int) -> None:
        self.logger.info("stopping_client", user_id=user_id)
        try:
            await self.client_manager.stop_client(user_id)
        except ClientNotFoundError:
            self.logger.exception("client_not_found", user_id=user_id)
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_ERROR,
                {"user_id": user_id, "error": "Client not found"},
            )

        self.logger.info("client_stopped", user_id=user_id)
        await self.publisher.publish(
            RabbitMQQueuePublisher.CLIENT_STOPPED,
            {"user_id": user_id},
        )

    async def get_chat_list(self, user_id: int) -> None:
        self.logger.info("getting_chat_list", user_id=user_id)
        try:
            chats = await self.client_manager.get_chat_list(user_id)
        except ClientNotFoundError:
            self.logger.exception("client_not_found", user_id=user_id)
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_ERROR,
                {"user_id": user_id, "error": "Client not found"},
            )
            return

        self.logger.info("chat_list_received", user_id=user_id)
        await self.publisher.publish(
            RabbitMQQueuePublisher.CLIENT_CHAT_LIST,
            {"user_id": user_id, "chats": [chat.model_dump() for chat in chats]},
        )
