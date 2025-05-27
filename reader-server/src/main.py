import asyncio
import json

import aio_pika
import structlog

from src.application import BatchCollectorManager, MessageProcessor
from src.core import settings
from src.domain import Message
from src.infrastructure import AnswerTaskPublisher, SentenceTransformerService

logger = structlog.get_logger()


async def process_message(
    message: aio_pika.IncomingMessage,
    batcher: BatchCollectorManager,
) -> None:
    async with message.process():
        try:
            msg_data = json.loads(message.body.decode())
            msg = Message(**msg_data)
            logger.info(
                "processing_message",
                message_id=msg.telegram_message_id,
                user_id=msg.user_id,
                chat_id=msg.chat_id,
            )
            await batcher.add(msg)
        except Exception as e:
            logger.exception(
                "message_processing_error",
                error=str(e),
                body=message.body.decode(),
            )
            raise


async def main() -> None:
    logger.info("starting_application")
    try:
        # Initialize services
        logger.info("initializing_services")
        embedding_service = SentenceTransformerService()
        publisher = AnswerTaskPublisher()
        await publisher.connect()
        logger.info("services_initialized")

        message_processor = MessageProcessor(embedding_service, publisher)

        # Initialize batch processing
        logger.info(
            "initializing_batch_processing",
            batch_size=settings.BATCH_SIZE,
            batch_time=settings.BATCH_TIME,
        )
        batcher = BatchCollectorManager(
            settings.BATCH_SIZE,
            settings.BATCH_TIME,
            message_processor.process_messages,
        )

        # Setup RabbitMQ
        logger.info("connecting_to_rabbitmq", url=settings.rabbitmq.url)
        connection = await aio_pika.connect_robust(settings.rabbitmq.url)
        channel = await connection.channel()
        queue = await channel.declare_queue(
            settings.MESSAGE_QUEUE_NAME,
            durable=True,
        )
        logger.info("rabbitmq_connected")

        # Start consuming messages
        logger.info("starting_message_consumption")
        await queue.consume(
            lambda message: process_message(message, batcher),
        )
        logger.info("message_consumption_started")

        await asyncio.Future()  # run forever
    except Exception as e:
        logger.exception("application_error", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
