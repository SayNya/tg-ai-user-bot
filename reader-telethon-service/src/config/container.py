from dependency_injector import containers, providers
from redis.asyncio import Redis

from src.handlers import RegistrationHandlers
from src.rabbitmq import RabbitMQPublisher, start_consumer
from src.services import TelethonRegistrationService


class Container(containers.DeclarativeContainer):
    """Application container."""

    config = providers.Configuration()

    # Redis client
    redis_client = providers.Singleton(
        Redis,
        url=config.redis.url,
    )

    # RabbitMQ connection
    rabbitmq_connection = providers.Resource(
        start_consumer,
    )

    rabbitmq_publisher = providers.Singleton(
        RabbitMQPublisher,
        url=config.rabbitmq.url,
    )

    # Services
    registration_service = providers.Factory(
        TelethonRegistrationService,
        redis_client=redis_client,
        publisher=rabbitmq_publisher,
    )

    # Handlers
    registration_handlers = providers.Factory(
        RegistrationHandlers,
        registration_service=registration_service,
    )
