import aio_pika

from src.config import Container, settings
from src.rabbitmq import QueueName
from src.utils.logging import setup_logger

logger = setup_logger().bind(module="rabbitmq_consumer")


async def start_consumer(container: Container) -> aio_pika.RobustConnection:
    logger.info("starting_rabbitmq_consumer")
    connection = await aio_pika.connect_robust(settings.rabbitmq.url)
    logger.info("rabbitmq_connected")

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    logger.info("channel_configured", prefetch_count=10)

    handlers = container.registration_handlers()
    logger.info("handlers_initialized")

    # Declare queues
    logger.info("declaring_queues")
    init_queue = await channel.declare_queue(QueueName.TELEGRAM_INIT, durable=True)
    confirm_queue = await channel.declare_queue(
        QueueName.TELEGRAM_CONFIRM,
        durable=True,
    )
    password_queue = await channel.declare_queue(
        QueueName.TELEGRAM_PASSWORD,
        durable=True,
    )
    logger.info(
        "queues_declared",
        queues=[
            QueueName.TELEGRAM_INIT,
            QueueName.TELEGRAM_CONFIRM,
            QueueName.TELEGRAM_PASSWORD,
        ],
    )

    # Set up consumers with injected handlers
    logger.info("setting_up_consumers")
    await init_queue.consume(handlers.handle_init)
    await confirm_queue.consume(handlers.handle_confirm)
    await password_queue.consume(handlers.handle_password_confirm)
    logger.info("consumers_setup_complete")

    return connection
