from src.services import ClientService


class ClientHandlers:
    def __init__(self, client_service: ClientService) -> None:
        self.service = client_service

    async def handle_start_client(self, payload: dict) -> None:
        await self.service.start_client(payload["user_id"])

    async def handle_stop_client(self, payload: dict) -> None:
        await self.service.stop_client(payload["user_id"])
