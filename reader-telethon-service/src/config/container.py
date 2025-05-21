from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db.repositories import ChatRepository, TelegramAuthRepository
from src.handlers import MessageHandlers, RegistrationHandlers
from src.infrastructure import (
    RabbitMQConsumer,
    RabbitMQPublisher,
    RedisClient,
    TelethonClientManager,
)
from src.services import MessageService, TelethonRegistrationService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Redis
    redis_raw_client = providers.Singleton(
        Redis,
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        decode_responses=True,
    )
    redis_client = providers.Singleton(
        RedisClient,
        redis=redis_raw_client,
    )

    # RabbitMQ
    rabbitmq_publisher = providers.Singleton(
        RabbitMQPublisher,
        connection_url=config.rabbitmq.url,
    )

    # DB
    db_engine = providers.Singleton(create_async_engine, url=config.database.url)
    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
    )

    # Repositories
    chat_repository = providers.Singleton(
        ChatRepository,
        session_factory=session_factory,
    )
    telegram_auth_repository = providers.Singleton(
        TelegramAuthRepository,
        session_factory=session_factory,
    )

    # Telegram
    client_manager = providers.Singleton(
        TelethonClientManager,
        telegram_auth_repository=telegram_auth_repository,
        publisher=rabbitmq_publisher,
        chat_repository=chat_repository,
    )

    # Registration
    registration_service = providers.Singleton(
        TelethonRegistrationService,
        redis_client=redis_client,
        publisher=rabbitmq_publisher,
        telegram_auth_repository=telegram_auth_repository,
    )
    registration_handlers = providers.Singleton(
        RegistrationHandlers,
        registration_service=registration_service,
    )
    registration_consumer = providers.Factory(
        RabbitMQConsumer,
        connection_url=config.rabbitmq.url,
        queue_handlers={
            "telegram.init": registration_handlers.provided.handle_init,
            "telegram.confirm": registration_handlers.provided.handle_confirm,
            "telegram.password": registration_handlers.provided.handle_password,
        },
    )

    # Message
    message_service = providers.Singleton(
        MessageService,
        client_manager=client_manager,
    )
    message_handlers = providers.Singleton(
        MessageHandlers,
        message_service=message_service,
    )
    message_consumer = providers.Factory(
        RabbitMQConsumer,
        connection_url=config.rabbitmq.url,
        queue_handlers={
            "message.answer": message_handlers.provided.handle_message,
        },
    )

    # Health checks
    redis_health_check = providers.Singleton(
        lambda redis: redis.ping(),
        redis=redis_raw_client,
    )

    rabbitmq_health_check = providers.Singleton(
        lambda publisher: publisher.connection.is_open,
        publisher=rabbitmq_publisher,
    )

    # Shutdown hooks
    shutdown_hooks = providers.List(
        providers.Callable(lambda redis: redis.close(), redis=redis_raw_client),
        providers.Callable(
            lambda publisher: publisher.connection.close(),
            publisher=rabbitmq_publisher,
        ),
        providers.Callable(lambda engine: engine.dispose(), engine=db_engine),
    )
