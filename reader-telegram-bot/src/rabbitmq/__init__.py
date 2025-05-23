from src.rabbitmq.consumer_registry import register_consumer, registry
from src.rabbitmq.consumers import client, registration

__all__ = ["client", "register_consumer", "registration", "registry"]
