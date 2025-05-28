from src.rabbitmq.consumer_registry import register_consumer, registry
from src.rabbitmq.consumers import chat, client, registration

__all__ = ["chat", "client", "register_consumer", "registration", "registry"]
