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
    ) -> None:
        self.client_manager = client_manager
        self.publisher = publisher

    async def start_client(self, user_id: int) -> None:
        try:
            client = await self.client_manager.start_client_by_user_id(user_id)
        except DatabaseNotFoundError:
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_ERROR,
                {"user_id": user_id, "error": "Client not found"},
            )
            return

        await self.publisher.publish(
            RabbitMQQueuePublisher.CLIENT_STARTED,
            {"user_id": user_id, "client": client},
        )

    async def stop_client(self, user_id: int) -> None:
        try:
            await self.client_manager.stop_client(user_id)
        except ClientNotFoundError:
            await self.publisher.publish(
                RabbitMQQueuePublisher.CLIENT_ERROR,
                {"user_id": user_id, "error": "Client not found"},
            )

        await self.publisher.publish(
            RabbitMQQueuePublisher.CLIENT_STOPPED,
            {"user_id": user_id},
        )
