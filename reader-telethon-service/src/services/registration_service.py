import asyncio

from redis.asyncio import Redis
from sqlalchemy import select
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession

from src.db.session import async_session_factory
from src.db.tables import TelegramAuth, User
from src.models.enums import ErrorCode, RegistrationStatus
from src.rabbitmq import QueueName, RabbitMQPublisher
from src.services.exceptions import (AuthDataExpiredError, RegistrationError,
                                     TelegramClientError)
from src.utils.logging import setup_logger

logger = setup_logger().bind(module="registration_service")


class TelethonRegistrationService:
    def __init__(
        self,
        redis_client: Redis,
        publisher: RabbitMQPublisher,
    ) -> None:
        self._clients: dict[int, TelegramClient] = {}
        self.background_tasks: set[asyncio.Task] = set()
        self.publisher = publisher
        self.redis_client = redis_client
        logger.info("registration_service_initialized")

    async def send_code(
        self,
        user_id: int,
        phone: str,
        api_id: int,
        api_hash: str,
    ) -> None:
        logger.info("sending_verification_code", user_id=user_id, phone=phone)
        session = StringSession()
        client = TelegramClient(session, api_id, api_hash)

        try:
            await client.connect()
            sent = await client.send_code_request(phone)
            logger.info("verification_code_sent", user_id=user_id)

            await self.publisher.publish(
                QueueName.TELEGRAM_STATUS,
                message={"user_id": user_id, "status": RegistrationStatus.CODE_SENT},
            )

            # Store auth data in Redis
            await self._store_auth_data(
                user_id=user_id,
                api_id=api_id,
                api_hash=api_hash,
                phone=phone,
                phone_code_hash=sent.phone_code_hash,
            )

            self._clients[user_id] = client
            self._schedule_client_expiration(user_id)
            logger.info("auth_data_stored", user_id=user_id)

        except Exception as e:
            logger.error("failed_to_send_code", user_id=user_id, error=str(e))
            await client.disconnect()
            raise TelegramClientError(f"Failed to send verification code: {e!s}")

    async def confirm_code(self, user_id: int, code: str) -> None:
        logger.info("confirming_code", user_id=user_id)
        client, auth_data = await self._get_auth_context(user_id)

        if not auth_data or not client:
            logger.warning("auth_data_expired", user_id=user_id)
            await self._handle_expired_auth(user_id)
            return

        try:
            await client.sign_in(
                phone=auth_data["phone"],
                code=code,
                phone_code_hash=auth_data["phone_code_hash"],
            )
            logger.info("code_confirmed", user_id=user_id)

            await self._complete_registration(
                user_id=user_id,
                client=client,
                auth_data=auth_data,
            )

        except SessionPasswordNeededError:
            logger.info("password_required", user_id=user_id)
            await self.publisher.publish(
                QueueName.TELEGRAM_STATUS,
                message={
                    "user_id": user_id,
                    "status": RegistrationStatus.PASSWORD_REQUIRED,
                },
            )
        except Exception as e:
            logger.error("code_confirmation_failed", user_id=user_id, error=str(e))
            raise RegistrationError(f"Failed to confirm code: {e!s}")

    async def _store_auth_data(
        self,
        user_id: int,
        api_id: int,
        api_hash: str,
        phone: str,
        phone_code_hash: str,
    ) -> None:
        logger.debug("storing_auth_data", user_id=user_id)
        await self.redis_client.hset(
            f"auth:{user_id}",
            mapping={
                "api_id": api_id,
                "api_hash": api_hash,
                "phone": phone,
                "phone_code_hash": phone_code_hash,
            },
        )
        await self.redis_client.expire(f"auth:{user_id}", 300)  # 5 minutes TTL

    async def _handle_expired_auth(self, user_id: int) -> None:
        logger.warning("handling_expired_auth", user_id=user_id)
        await self.publisher.publish(
            QueueName.TELEGRAM_STATUS,
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
        user_id: int,
        client: TelegramClient,
        auth_data: dict,
    ) -> None:
        logger.info("completing_registration", user_id=user_id)
        session_string = client.session.save()
        await self._save_session(
            user_id=user_id,
            api_id=int(auth_data["api_id"]),
            api_hash=auth_data["api_hash"],
            phone=auth_data["phone"],
            session_string=session_string,
        )

        await client.disconnect()
        await self.redis_client.delete(f"auth:{user_id}")
        logger.info("registration_completed", user_id=user_id)

        await self.publisher.publish(
            QueueName.TELEGRAM_STATUS,
            message={
                "user_id": user_id,
                "status": RegistrationStatus.REGISTERED,
            },
        )

    def _schedule_client_expiration(self, user_id: int) -> None:
        logger.debug("scheduling_client_expiration", user_id=user_id)
        task = asyncio.create_task(self._expire_client(user_id, timeout=300))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def confirm_password(self, user_id: int, password: str) -> None:
        logger.info("confirming_password", user_id=user_id)
        client, auth_data = await self._get_auth_context(user_id)

        if not auth_data or not client:
            logger.warning("auth_data_expired_password", user_id=user_id)
            await self.publisher.publish(
                QueueName.TELEGRAM_STATUS,
                message={
                    "user_id": user_id,
                    "status": RegistrationStatus.ERROR,
                    "error": {
                        "code": ErrorCode.AUTH_DATA_EXPIRED,
                        "message": "Срок действия авторизационных данных истёк, пожалуйста, повторите регистрацию",
                    },
                },
            )
            return

        api_id = int(auth_data["api_id"])
        api_hash = auth_data["api_hash"]
        phone = auth_data["phone"]

        try:
            await client.sign_in(password=password)
            logger.info("password_confirmed", user_id=user_id)
        except Exception as e:
            logger.exception("password_confirmation_failed", user_id=user_id, error=str(e))
            await client.disconnect()
            raise e

        session_string = client.session.save()
        await self._save_session(
            user_id=user_id,
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            session_string=session_string,
        )
        await client.disconnect()
        await self.redis_client.delete(f"auth:{user_id}")
        logger.info("registration_completed_with_password", user_id=user_id)

        await self.publisher.publish(
            QueueName.TELEGRAM_STATUS,
            message={
                "user_id": user_id,
                "status": RegistrationStatus.REGISTERED,
            },
        )

    async def _get_auth_context(
        self,
        user_id: int,
    ) -> tuple[TelegramClient | None, dict | None]:
        client = self._clients.get(user_id)
        auth_data = await self.redis_client.hgetall(f"auth:{user_id}")
        return client, auth_data

    @staticmethod
    async def _save_session(
        user_id: int,
        api_id: int,
        api_hash: str,
        phone: str,
        session_string: str,
    ) -> None:
        logger.debug("saving_session", user_id=user_id)
        async with async_session_factory() as session_db:
            stmt = select(User).where(User.telegram_user_id == user_id)
            result = await session_db.scalars(stmt)
            user = result.first()

            tg_auth = TelegramAuth(
                api_id=api_id,
                api_hash=api_hash,
                phone=phone,
                session_string=session_string,
                user=user,
            )
            session_db.add(tg_auth)
            await session_db.commit()
            logger.debug("session_saved", user_id=user_id)

    async def _expire_client(self, user_id: int, timeout: int) -> None:
        logger.debug("expiring_client", user_id=user_id, timeout=timeout)
        await asyncio.sleep(timeout)
        client = self._clients.pop(user_id, None)
        if client:
            try:
                await client.disconnect()
                logger.debug("client_disconnected", user_id=user_id)
            except Exception as e:
                logger.error(
                    "failed_to_disconnect_client",
                    user_id=user_id,
                    error=str(e),
                )
