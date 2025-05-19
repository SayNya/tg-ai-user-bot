import json

from aio_pika import IncomingMessage

from src.services.registration_service import RegistrationService
from src.utils.logging import setup_logger

logger = setup_logger().bind(module="registration_handlers")


class RegistrationHandlers:
    def __init__(self, registration_service: RegistrationService) -> None:
        self.service = registration_service
        logger.info("registration_handlers_initialized")

    async def handle_init(self, message: IncomingMessage) -> None:
        logger.info("processing_init_message", message_id=message.message_id)
        async with message.process():
            data = json.loads(message.body)
            user_id = data["user_id"]
            phone = data["phone"]
            api_id = data["api_id"]
            api_hash = data["api_hash"]

            logger.info(
                "init_message_data_extracted",
                user_id=user_id,
                phone=phone,
                api_id=api_id,
            )

            await self.service.send_code(user_id, phone, api_id, api_hash)
            logger.info("init_message_processed", message_id=message.message_id)

    async def handle_confirm(self, message: IncomingMessage) -> None:
        logger.info("processing_confirm_message", message_id=message.message_id)
        async with message.process():
            data = json.loads(message.body)
            user_id = data["user_id"]
            code = data["code"]

            logger.info("confirm_message_data_extracted", user_id=user_id)

            await self.service.confirm_code(user_id, code)
            logger.info("confirm_message_processed", message_id=message.message_id)

    async def handle_password_confirm(self, message: IncomingMessage) -> None:
        logger.info(
            "processing_password_confirm_message",
            message_id=message.message_id,
        )
        async with message.process():
            data = json.loads(message.body)
            user_id = data["user_id"]
            password = data["password"]

            logger.info("password_confirm_message_data_extracted", user_id=user_id)

            await self.service.confirm_password(user_id, password)
            logger.info(
                "password_confirm_message_processed",
                message_id=message.message_id,
            )
