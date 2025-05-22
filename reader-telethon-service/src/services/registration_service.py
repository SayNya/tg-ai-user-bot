import asyncio

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from src.db.repositories import TelegramAuthRepository
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
    ) -> None:
        self._clients: dict[int, TelegramClient] = {}
        self.background_tasks: set[asyncio.Task] = set()
        self.publisher = publisher
        self.redis_client = redis_client
        self._telegram_auth_repository = telegram_auth_repository

    async def send_code(
        self,
        model: RegistrationInit,
    ) -> None:
        session = StringSession()
        client = TelegramClient(session, model.api_id, model.api_hash)

        try:
            await client.connect()
            sent = await client.send_code_request(model.phone)

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
            await client.disconnect()
            raise TelegramClientError(f"Failed to send verification code: {e!s}")

    async def confirm_code(self, model: RegistrationConfirm) -> None:
        client, auth_data = await self._get_auth_context(model.user_id)

        if not auth_data or not client:
            await self._handle_expired_auth(model.user_id)
            return

        try:
            await client.sign_in(
                phone=auth_data.phone,
                code=model.code,
                phone_code_hash=auth_data.phone_code_hash,
            )

            await self._complete_registration(
                user_id=model.user_id,
                client=client,
                auth_data=auth_data,
            )

        except SessionPasswordNeededError:
            await self.publisher.publish(
                RabbitMQQueuePublisher.REGISTRATION_STATUS,
                message={
                    "user_id": model.user_id,
                    "status": RegistrationStatus.PASSWORD_REQUIRED,
                },
            )
        except Exception as e:
            raise RegistrationError(f"Failed to confirm code: {e!s}")

    async def _store_auth_data(
        self,
        auth_data: AuthData,
    ) -> None:
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
        task = asyncio.create_task(self._expire_client(user_id, timeout=300))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def confirm_password(self, model: RegistrationPasswordConfirm) -> None:
        client, auth_data = await self._get_auth_context(model.user_id)

        if not auth_data or not client:
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
        except Exception as e:
            await client.disconnect()
            raise e

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

    async def _get_auth_context(
        self,
        user_id: int,
    ) -> tuple[TelegramClient | None, AuthData | None]:
        client = self._clients.get(user_id)
        auth_data = await self.redis_client.hgetall(f"auth:{user_id}")
        if auth_data:
            auth_data = AuthData(**auth_data)
        return client, auth_data

    async def _save_session(
        self,
        auth_data: AuthData,
        session_string: str,
    ) -> None:
        tg_auth_create = TelegramAuthCreate(
            api_id=auth_data.api_id,
            api_hash=auth_data.api_hash,
            phone=auth_data.phone,
            session_string=session_string,
            user_id=auth_data.user_id,
        )
        await self._telegram_auth_repository.create(tg_auth_create)

    async def _expire_client(self, user_id: int, timeout: int) -> None:
        await asyncio.sleep(timeout)
        client = self._clients.pop(user_id, None)
        if client:
            try:
                await client.disconnect()
            except Exception as e:
                raise e
