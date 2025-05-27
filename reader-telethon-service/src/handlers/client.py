import structlog

from src.services import ClientService


class ClientHandlers:
    def __init__(
        self,
        client_service: ClientService,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.service = client_service
        self.logger = logger

    async def handle_start_client(self, payload: dict) -> None:
        self.logger.info(
            "handle_start_client_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            await self.service.start_client(payload["user_id"])
        except Exception as e:
            self.logger.exception(
                "handle_start_client_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise

    async def handle_stop_client(self, payload: dict) -> None:
        self.logger.info(
            "handle_stop_client_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            await self.service.stop_client(payload["user_id"])
        except Exception as e:
            self.logger.exception(
                "handle_stop_client_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise
