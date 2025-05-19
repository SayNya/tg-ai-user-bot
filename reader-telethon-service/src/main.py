import asyncio
import logging

from src.config.container import Container
from src.utils.logging import setup_logger


async def main() -> None:
    # Setup logging
    logger = setup_logger().bind(type="main")

    # Suppress noisy logs
    for noisy in ["httpcore", "httpx", "aio_pika"]:
        logging.getLogger(noisy).setLevel(logging.CRITICAL + 1)

    container = Container()
    container.init_resources()

    logger.debug("Starting RabbitMQ consumer")
    connection = await container.rabbitmq_connection(container)
    logger.info("Service is running. Waiting for messages...")

    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()
        container.shutdown_resources()
        logger.info("RabbitMQ connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
