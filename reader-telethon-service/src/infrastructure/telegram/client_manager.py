from src.db.repositories import ChatRepository, TelegramAuthRepository
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from src.models.database import TelegramAuth as TelegramAuthModel

from .client_wrapper import TelethonClientWrapper


class TelethonClientManager:
    def __init__(
        self,
        telegram_auth_repository: TelegramAuthRepository,
        publisher: RabbitMQPublisher,
        chat_repository: ChatRepository,
    ) -> None:
        self._registry: dict[int, TelethonClientWrapper] = {}
        self._publisher = publisher
        self._chat_repository = chat_repository
        self._telegram_auth_repository = telegram_auth_repository

    def _create_client(self, auth_model: TelegramAuthModel) -> TelethonClientWrapper:
        return TelethonClientWrapper(
            user_id=auth_model.user_id,
            api_id=auth_model.api_id,
            api_hash=auth_model.api_hash,
            session_string=auth_model.session_string,
            publisher=self._publisher,
            chat_repository=self._chat_repository,
        )

    async def _start_client(
        self,
        auth_model: TelegramAuthModel,
    ) -> TelethonClientWrapper:
        client = self._create_client(auth_model)
        await client.start()
        self._registry[auth_model.user_id] = client
        return client

    async def start_client_by_user_id(self, user_id: int) -> TelethonClientWrapper:
        auth = await self._telegram_auth_repository.get_by_user_id(user_id)
        if not auth:
            raise ValueError(f"No session found for user {user_id}")

        return await self._start_client(auth)

    async def start_all_clients(self) -> None:
        async for auth in self._telegram_auth_repository.all():
            if auth.session_string:
                await self._start_client(auth)

    def get_client(self, user_id: int) -> TelethonClientWrapper | None:
        return self._registry.get(user_id)

    async def stop_client(self, user_id: int) -> None:
        client = self._registry.pop(user_id, None)
        if client:
            await client.stop()

    async def stop_all_clients(self) -> None:
        for user_id in list(self._registry.keys()):
            await self.stop_client(user_id)
