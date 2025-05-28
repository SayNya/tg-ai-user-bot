import structlog

from src.db.repositories import ChatRepository, TelegramAuthRepository, UserRepository
from src.exceptions import ClientNotFoundError
from src.infrastructure.rabbitmq.publisher import RabbitMQPublisher
from src.models.database import TelegramAuth as TelegramAuthModel
from src.models.domain import ChatModel
from .client_wrapper import TelethonClientWrapper


class TelethonClientManager:
    def __init__(
        self,
        telegram_auth_repository: TelegramAuthRepository,
        publisher: RabbitMQPublisher,
        chat_repository: ChatRepository,
        user_repository: UserRepository,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._registry: dict[int, TelethonClientWrapper] = {}
        self._publisher = publisher
        self._chat_repository = chat_repository
        self._telegram_auth_repository = telegram_auth_repository
        self._user_repository = user_repository
        self.logger = logger

    def _create_client(self, auth_model: TelegramAuthModel) -> TelethonClientWrapper:
        self.logger.debug(
            "creating_client",
            user_id=auth_model.user_id,
        )
        return TelethonClientWrapper(
            user_id=auth_model.user_id,
            api_id=auth_model.api_id,
            api_hash=auth_model.api_hash,
            session_string=auth_model.session_string,
            publisher=self._publisher,
            chat_repository=self._chat_repository,
            logger=self.logger,
        )

    async def _start_client(
        self,
        auth_model: TelegramAuthModel,
    ) -> TelethonClientWrapper:
        self.logger.info(
            "starting_client",
            user_id=auth_model.user_id,
        )
        client = self._create_client(auth_model)
        await client.start()
        self._registry[auth_model.user_id] = client
        self.logger.info(
            "client_started",
            user_id=auth_model.user_id,
        )
        return client

    async def start_client_by_telegram_user_id(
        self,
        telegram_user_id: int,
    ) -> TelethonClientWrapper:
        self.logger.info(
            "starting_client_by_telegram_id",
            telegram_user_id=telegram_user_id,
        )
        user = await self._user_repository.get_by_telegram_user_id(telegram_user_id)
        auth = await self._telegram_auth_repository.get_by_user_id(user.id)
        return await self._start_client(auth)

    async def start_all_clients(self) -> None:
        self.logger.info("starting_all_clients")
        async for auth in self._telegram_auth_repository.all():
            if auth.session_string:
                try:
                    await self._start_client(auth)
                except Exception as e:
                    self.logger.exception(
                        "failed_to_start_client",
                        user_id=auth.user_id,
                        error=str(e),
                    )

    def get_client(self, user_id: int) -> TelethonClientWrapper | None:
        client = self._registry.get(user_id)
        if not client:
            self.logger.debug(
                "client_not_found",
                user_id=user_id,
            )
        return client

    def get_registry(self) -> dict[int, TelethonClientWrapper]:
        return self._registry

    async def stop_client(self, user_id: int) -> None:
        self.logger.info(
            "stopping_client",
            user_id=user_id,
        )
        client = self._registry.pop(user_id, None)
        if not client:
            self.logger.error(
                "client_not_found",
                user_id=user_id,
            )
            raise ClientNotFoundError

        await client.stop()
        self.logger.info(
            "client_stopped",
            user_id=user_id,
        )

    async def stop_all_clients(self) -> None:
        self.logger.info("stopping_all_clients")
        for user_id in list(self._registry.keys()):
            try:
                await self.stop_client(user_id)
            except Exception as e:
                self.logger.exception(
                    "failed_to_stop_client",
                    user_id=user_id,
                    error=str(e),
                )

    async def get_chat_list(self, telegram_user_id: int) -> list[ChatModel]:
        user = await self._user_repository.get_by_telegram_user_id(telegram_user_id)
        client = self.get_client(user.id)
        if not client:
            raise ClientNotFoundError
        return await client.get_chat_list()
