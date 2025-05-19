from src.rabbitmq.consumer_registry import registry
from src.rabbitmq.consumers import registration_consumer

__all__ = ["registration_consumer", "registry"]
