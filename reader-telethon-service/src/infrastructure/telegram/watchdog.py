import asyncio

import structlog

from src.infrastructure import RabbitMQPublisher
from src.models.enums.infrastructure import RabbitMQQueuePublisher

from .client_manager import TelethonClientManager


class ClientWatchdog:
    def __init__(
        self,
        client_manager: TelethonClientManager,
        publisher: RabbitMQPublisher,
        logger: structlog.typing.FilteringBoundLogger,
        check_interval: int = 10,
    ) -> None:
        self.client_manager = client_manager
        self.publisher = publisher
        self.check_interval = check_interval
        self.disconnected_clients: set[int] = set()
        self.logger = logger

    async def run(self) -> None:
        self.logger.info(
            "starting_watchdog",
            check_interval=self.check_interval,
        )
        while True:
            try:
                await self._check_clients()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.exception(
                    "watchdog_error",
                    error=str(e),
                )

    async def _check_clients(self) -> None:
        for user_id, client_wrapper in self.client_manager.get_registry().items():
            try:
                if not client_wrapper.client.is_connected():
                    if user_id not in self.disconnected_clients:
                        self.logger.warning(
                            "client_disconnected",
                            user_id=user_id,
                        )
                        await self.publisher.publish(
                            RabbitMQQueuePublisher.CLIENT_STATUS,
                            {"user_id": user_id, "event": "disconnected"},
                        )
                        self.disconnected_clients.add(user_id)
                elif user_id in self.disconnected_clients:
                    self.logger.info(
                        "client_reconnected",
                        user_id=user_id,
                    )
                    await self.publisher.publish(
                        RabbitMQQueuePublisher.CLIENT_STATUS,
                        {"user_id": user_id, "event": "reconnected"},
                    )
                    self.disconnected_clients.remove(user_id)
            except Exception as e:
                self.logger.exception(
                    "client_check_error",
                    user_id=user_id,
                    error=str(e),
                )
