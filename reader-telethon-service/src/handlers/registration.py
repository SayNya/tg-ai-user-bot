from src.models.domain import (
    RegistrationConfirm,
    RegistrationInit,
    RegistrationPasswordConfirm,
)
from src.services import TelethonRegistrationService


class RegistrationHandlers:
    def __init__(self, registration_service: TelethonRegistrationService) -> None:
        self.service = registration_service

    async def handle_init(self, payload: dict) -> None:
        model = RegistrationInit(**payload)

        await self.service.send_code(model)

    async def handle_confirm(self, payload: dict) -> None:
        model = RegistrationConfirm(**payload)

        await self.service.confirm_code(model)

    async def handle_password_confirm(self, payload: dict) -> None:
        model = RegistrationPasswordConfirm(**payload)

        await self.service.confirm_password(model)
