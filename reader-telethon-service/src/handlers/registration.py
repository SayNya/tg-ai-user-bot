import structlog

from src.models.domain import (
    RegistrationConfirm,
    RegistrationInit,
    RegistrationPasswordConfirm,
)
from src.services import TelethonRegistrationService


class RegistrationHandlers:
    def __init__(
        self,
        registration_service: TelethonRegistrationService,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.service = registration_service
        self.logger = logger

    async def handle_init(self, payload: dict) -> None:
        self.logger.info(
            "handle_init_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = RegistrationInit(**payload)
            await self.service.send_code(model)
        except Exception as e:
            self.logger.exception(
                "handle_init_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise

    async def handle_confirm(self, payload: dict) -> None:
        self.logger.info(
            "handle_confirm_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = RegistrationConfirm(**payload)
            await self.service.confirm_code(model)
        except Exception as e:
            self.logger.exception(
                "handle_confirm_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise

    async def handle_password_confirm(self, payload: dict) -> None:
        self.logger.info(
            "handle_password_confirm_called",
            payload=payload,
            user_id=payload.get("user_id"),
        )
        try:
            model = RegistrationPasswordConfirm(**payload)
            await self.service.confirm_password(model)
        except Exception as e:
            self.logger.exception(
                "handle_password_confirm_error",
                user_id=payload.get("user_id"),
                error=str(e),
            )
            raise
