import asyncio

import structlog
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from src.db.repositories import TelegramAuthRepository, UserRepository
from src.exceptions import (
    AuthDataExpiredError,
    RegistrationError,
    TelegramClientError,
)
from src.infrastructure import RabbitMQPublisher, RedisClient
from src.models.database import TelegramAuthCreate
from src.models.domain import (
    AuthData,
    RegistrationConfirm,
    RegistrationInit,
    RegistrationPasswordConfirm,
)
from src.models.enums import ErrorCode, RegistrationStatus
from src.models.enums.infrastructure import RabbitMQQueuePublisher


class TelethonRegistrationService:
    def __init__(
        self,
        redis_client: RedisClient,
        publisher: RabbitMQPublisher,
        telegram_auth_repository: TelegramAuthRepository,
        user_repository: UserRepository,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self._clients: dict[int, TelegramClient] = {}
        self.background_tasks: set[asyncio.Task] = set()
        self.publisher = publisher
        self.redis_client = redis_client
        self._telegram_auth_repository = telegram_auth_repository
        self._user_repository = user_repository
        self.logger = logger

    async def send_code(
        self,
        model: RegistrationInit,
    ) -> None:
        self.logger.info(
            "sending_verification_code",
            user_id=model.user_id,
            phone=model.phone,
        )
        session = StringSession()
        client = TelegramClient(session, model.api_id, model.api_hash)

        try:
            await client.connect()
            sent = await client.send_code_request(model.phone)

            self.logger.info(
                "verification_code_sent",
                user_id=model.user_id,
                phone=model.phone,
            )

            await self.publisher.publish(
                RabbitMQQueuePublisher.REGISTRATION_STATUS,
                message={
                    "user_id": model.user_id,
                    "status": RegistrationStatus.CODE_SENT,
                },
            )

            auth_data = AuthData(
                user_id=model.user_id,
                phone=model.phone,
                api_id=model.api_id,
                api_hash=model.api_hash,
                phone_code_hash=sent.phone_code_hash,
            )

            await self._store_auth_data(auth_data)

            self._clients[model.user_id] = client
            self._schedule_client_expiration(model.user_id)

        except Exception as e:
            self.logger.error(
                "failed_to_send_code",
                user_id=model.user_id,
                error=str(e),
            )
            await client.disconnect()
            raise TelegramClientError(f"Failed to send verification code: {e!s}")

    async def confirm_code(self, model: RegistrationConfirm) -> None:
        self.logger.info(
            "confirming_code",
            user_id=model.user_id,
        )
        client, auth_data = await self._get_auth_context(model.user_id)

        if not auth_data or not client:
            self.logger.error(
                "auth_context_not_found",
                user_id=model.user_id,
            )
            await self._handle_expired_auth(model.user_id)
            return

        try:
            await client.sign_in(
                phone=auth_data.phone,
                code=model.code,
                phone_code_hash=auth_data.phone_code_hash,
            )

            self.logger.info(
                "code_confirmed",
                user_id=model.user_id,
            )

            await self._complete_registration(
                user_id=model.user_id,
                client=client,
                auth_data=auth_data,
            )

        except SessionPasswordNeededError:
            self.logger.info(
                "password_required",
                user_id=model.user_id,
            )
            await self.publisher.publish(
                RabbitMQQueuePublisher.REGISTRATION_STATUS,
                message={
                    "user_id": model.user_id,
                    "status": RegistrationStatus.PASSWORD_REQUIRED,
                },
            )
        except Exception as e:
            self.logger.error(
                "code_confirmation_failed",
                user_id=model.user_id,
                error=str(e),
            )
            raise RegistrationError(f"Failed to confirm code: {e!s}")

    async def confirm_password(self, model: RegistrationPasswordConfirm) -> None:
        self.logger.info(
            "confirming_password",
            user_id=model.user_id,
        )
        client, auth_data = await self._get_auth_context(model.user_id)

        if not auth_data or not client:
            self.logger.error(
                "auth_context_not_found",
                user_id=model.user_id,
            )
            await self.publisher.publish(
                RabbitMQQueuePublisher.REGISTRATION_STATUS,
                message={
                    "user_id": model.user_id,
                    "status": RegistrationStatus.ERROR,
                    "error": {
                        "code": ErrorCode.AUTH_DATA_EXPIRED,
                        "message": "Срок действия авторизационных данных истёк, пожалуйста, повторите регистрацию",
                    },
                },
            )
            return

        try:
            await client.sign_in(password=model.password)
            self.logger.info(
                "password_confirmed",
                user_id=model.user_id,
            )
        except Exception as e:
            self.logger.error(
                "password_confirmation_failed",
                user_id=model.user_id,
                error=str(e),
            )
            await client.disconnect()
            raise e

        session_string = client.session.save()
        await self._save_session(
            auth_data=auth_data,
            session_string=session_string,
        )
        await client.disconnect()
        await self.redis_client.delete(f"auth:{auth_data.user_id}")

        self.logger.info(
            "registration_completed",
            user_id=auth_data.user_id,
        )

        await self.publisher.publish(
            RabbitMQQueuePublisher.REGISTRATION_STATUS,
            message={
                "user_id": auth_data.user_id,
                "status": RegistrationStatus.REGISTERED,
            },
        )

    async def _get_auth_context(
        self,
        user_id: int,
    ) -> tuple[TelegramClient | None, AuthData | None]:
        client = self._clients.get(user_id)
        auth_data = await self.redis_client.hgetall(f"auth:{user_id}")
        if auth_data:
            auth_data = AuthData(**auth_data, user_id=user_id)
        return client, auth_data

    async def _save_session(
        self,
        auth_data: AuthData,
        session_string: str,
    ) -> None:
        self.logger.debug(
            "saving_session",
            user_id=auth_data.user_id,
        )
        user = await self._user_repository.get_by_telegram_user_id(auth_data.user_id)
        tg_auth_create = TelegramAuthCreate(
            api_id=auth_data.api_id,
            api_hash=auth_data.api_hash,
            phone=auth_data.phone,
            session_string=session_string,
            user_id=user.id,
        )
        await self._telegram_auth_repository.create(tg_auth_create)

    async def _store_auth_data(
        self,
        auth_data: AuthData,
    ) -> None:
        self.logger.debug(
            "storing_auth_data",
            user_id=auth_data.user_id,
        )
        await self.redis_client.hset(
            f"auth:{auth_data.user_id}",
            mapping={
                "api_id": auth_data.api_id,
                "api_hash": auth_data.api_hash,
                "phone": auth_data.phone,
                "phone_code_hash": auth_data.phone_code_hash,
            },
        )
        await self.redis_client.expire(f"auth:{auth_data.user_id}", 300)

    async def _handle_expired_auth(self, user_id: int) -> None:
        self.logger.error(
            "auth_data_expired",
            user_id=user_id,
        )
        await self.publisher.publish(
            RabbitMQQueuePublisher.REGISTRATION_STATUS,
            message={
                "user_id": user_id,
                "status": RegistrationStatus.ERROR,
                "error": {
                    "code": ErrorCode.AUTH_DATA_EXPIRED,
                    "message": "Authentication data has expired. Please try registration again.",
                },
            },
        )
        raise AuthDataExpiredError("Authentication data has expired")

    async def _complete_registration(
        self,
        client: TelegramClient,
        auth_data: AuthData,
    ) -> None:
        self.logger.info(
            "completing_registration",
            user_id=auth_data.user_id,
        )
        session_string = client.session.save()
        await self._save_session(
            auth_data=auth_data,
            session_string=session_string,
        )

        await client.disconnect()
        await self.redis_client.delete(f"auth:{auth_data.user_id}")

        await self.publisher.publish(
            RabbitMQQueuePublisher.REGISTRATION_STATUS,
            message={
                "user_id": auth_data.user_id,
                "status": RegistrationStatus.REGISTERED,
            },
        )

    def _schedule_client_expiration(self, user_id: int) -> None:
        self.logger.debug(
            "scheduling_client_expiration",
            user_id=user_id,
        )
        task = asyncio.create_task(self._expire_client(user_id, timeout=300))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def _expire_client(self, user_id: int, timeout: int) -> None:
        await asyncio.sleep(timeout)
        client = self._clients.pop(user_id, None)
        if client:
            try:
                await client.disconnect()
                self.logger.debug(
                    "client_expired",
                    user_id=user_id,
                )
            except Exception as e:
                self.logger.error(
                    "client_expiration_error",
                    user_id=user_id,
                    error=str(e),
                )
                raise e
