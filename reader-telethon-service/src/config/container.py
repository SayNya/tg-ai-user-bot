import httpx
from dependency_injector import containers, providers
from openai import AsyncOpenAI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db.repositories import (
    ChatRepository,
    MessageRepository,
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
from src.utils import setup_logger


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Loggers
    db_logger = providers.Factory(
        setup_logger,
        logger_type="database",
        debug=config.debug,
    )
    rabbitmq_logger = providers.Factory(
        setup_logger,
        logger_type="rabbitmq",
        debug=config.debug,
    )
    telegram_logger = providers.Factory(
        setup_logger,
        logger_type="telegram",
        debug=config.debug,
    )
    redis_logger = providers.Factory(
        setup_logger,
        logger_type="redis",
        debug=config.debug,
    )
    service_logger = providers.Factory(
        setup_logger,
        logger_type="service",
        debug=config.debug,
    )
    handler_logger = providers.Factory(
        setup_logger,
        logger_type="handler",
        debug=config.debug,
    )

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
        logger=redis_logger,
    )

    # RabbitMQ
    rabbitmq_publisher = providers.Singleton(
        RabbitMQPublisher,
        connection_url=config.rabbitmq.url,
        logger=rabbitmq_logger,
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
        logger=db_logger,
    )
    telegram_auth_repository = providers.Singleton(
        TelegramAuthRepository,
        session_factory=session_factory,
        logger=db_logger,
    )
    topic_repository = providers.Singleton(
        TopicRepository,
        session_factory=session_factory,
        logger=db_logger,
    )
    user_repository = providers.Singleton(
        UserRepository,
        session_factory=session_factory,
        logger=db_logger,
    )
    message_repository = providers.Singleton(
        MessageRepository,
        session_factory=session_factory,
        logger=db_logger,
    )

    # OpenAI
    openai_proxy_client = providers.Singleton(
        httpx.AsyncClient,
        proxy=config.openai.proxy,
    )
    openai_client = providers.Singleton(
        AsyncOpenAI,
        api_key=config.openai.api_key,
        http_client=openai_proxy_client,
    )

    # Telegram
    client_manager = providers.Singleton(
        TelethonClientManager,
        telegram_auth_repository=telegram_auth_repository,
        publisher=rabbitmq_publisher,
        chat_repository=chat_repository,
        user_repository=user_repository,
        logger=telegram_logger,
    )
    watchdog = providers.Singleton(
        ClientWatchdog,
        client_manager=client_manager,
        publisher=rabbitmq_publisher,
        logger=telegram_logger,
    )

    # Registration
    registration_service = providers.Singleton(
        TelethonRegistrationService,
        redis_client=redis_client,
        publisher=rabbitmq_publisher,
        telegram_auth_repository=telegram_auth_repository,
        user_repository=user_repository,
        logger=service_logger,
    )
    registration_handlers = providers.Singleton(
        RegistrationHandlers,
        registration_service=registration_service,
        logger=handler_logger,
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
        logger=rabbitmq_logger,
    )
    # Message
    message_service = providers.Singleton(
        MessageService,
        client_manager=client_manager,
        topic_repository=topic_repository,
        message_repository=message_repository,
        chat_repository=chat_repository,
        openai_client=openai_client,
        logger=service_logger,
    )
    message_handlers = providers.Singleton(
        MessageHandlers,
        message_service=message_service,
        logger=handler_logger,
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
        logger=rabbitmq_logger,
    )

    # Client
    client_service = providers.Singleton(
        ClientService,
        client_manager=client_manager,
        publisher=rabbitmq_publisher,
        logger=service_logger,
    )
    client_handlers = providers.Singleton(
        ClientHandlers,
        client_service=client_service,
        logger=handler_logger,
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
        logger=rabbitmq_logger,
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
            lambda publisher: publisher.close(),
            publisher=rabbitmq_publisher,
        ),
        providers.Callable(lambda engine: engine.dispose(), engine=db_engine),
    )
