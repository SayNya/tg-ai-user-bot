from dependency_injector import containers, providers
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db.repositories import (
    ChatRepository,
    TelegramAuthRepository,
    TopicRepository,
    UserRepository,
)
from src.handlers import (
    ClientHandlers,
    MessageHandlers,
    RegistrationHandlers,
)
from src.infrastructure import (
    ClientWatchdog,
    RabbitMQConsumer,
    RabbitMQPublisher,
    RedisClient,
    TelethonClientManager,
)
from src.models.enums.infrastructure import RabbitMQQueueConsumer
from src.services import (
    ClientService,
    MessageService,
    TelethonRegistrationService,
)


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
    topic_repository = providers.Singleton(
        TopicRepository,
        session_factory=session_factory,
    )
    user_repository = providers.Singleton(
        UserRepository,
        session_factory=session_factory,
    )

    # Telegram
    client_manager = providers.Singleton(
        TelethonClientManager,
        telegram_auth_repository=telegram_auth_repository,
        publisher=rabbitmq_publisher,
        chat_repository=chat_repository,
        user_repository=user_repository,
    )
    watchdog = providers.Singleton(
        ClientWatchdog,
        client_manager=client_manager,
        publisher=rabbitmq_publisher,
    )

    # Registration
    registration_service = providers.Singleton(
        TelethonRegistrationService,
        redis_client=redis_client,
        publisher=rabbitmq_publisher,
        telegram_auth_repository=telegram_auth_repository,
        user_repository=user_repository,
    )
    registration_handlers = providers.Singleton(
        RegistrationHandlers,
        registration_service=registration_service,
    )
    registration_queue_handlers = providers.Callable(
        lambda handlers: {
            RabbitMQQueueConsumer.REGISTRATION_INIT: handlers.handle_init,
            RabbitMQQueueConsumer.REGISTRATION_CONFIRM: handlers.handle_confirm,
            RabbitMQQueueConsumer.REGISTRATION_PASSWORD: handlers.handle_password_confirm,
        },
        registration_handlers,
    )
    registration_consumer = providers.Factory(
        RabbitMQConsumer,
        connection_url=config.rabbitmq.url,
        queue_handlers=registration_queue_handlers,
    )
    # Message
    message_service = providers.Singleton(
        MessageService,
        client_manager=client_manager,
        topic_repository=topic_repository,
    )
    message_handlers = providers.Singleton(
        MessageHandlers,
        message_service=message_service,
    )
    message_queue_handlers = providers.Callable(
        lambda handlers: {
            RabbitMQQueueConsumer.MESSAGE_ANSWER: handlers.handle_answer,
        },
        message_handlers,
    )
    message_consumer = providers.Factory(
        RabbitMQConsumer,
        connection_url=config.rabbitmq.url,
        queue_handlers=message_queue_handlers,
    )

    # Client
    client_service = providers.Singleton(
        ClientService,
        client_manager=client_manager,
        publisher=rabbitmq_publisher,
    )
    client_handlers = providers.Singleton(
        ClientHandlers,
        client_service=client_service,
    )
    client_queue_handlers = providers.Callable(
        lambda handlers: {
            RabbitMQQueueConsumer.CLIENT_START: handlers.handle_start_client,
            RabbitMQQueueConsumer.CLIENT_STOP: handlers.handle_stop_client,
        },
        client_handlers,
    )
    client_consumer = providers.Factory(
        RabbitMQConsumer,
        connection_url=config.rabbitmq.url,
        queue_handlers=client_queue_handlers,
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
