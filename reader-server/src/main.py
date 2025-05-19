import asyncio
import json

import aio_pika

from src.application import BatchCollectorManager, MessageProcessor
from src.core import settings
from src.domain import Message
from src.infrastructure import AnswerTaskPublisher, SentenceTransformerService


async def process_message(
    message: aio_pika.IncomingMessage,
    batcher: BatchCollectorManager,
) -> None:
    async with message.process():
        msg_data = json.loads(message.body.decode())
        msg = Message(**msg_data)
        await batcher.add(msg)


async def main() -> None:
    # Initialize services
    embedding_service = SentenceTransformerService()
    publisher = AnswerTaskPublisher()
    await publisher.connect()

    message_processor = MessageProcessor(embedding_service, publisher)

    # Initialize batch processing
    batcher = BatchCollectorManager(
        settings.BATCH_SIZE,
        settings.BATCH_TIME,
        message_processor.process_messages,
    )

    # Setup RabbitMQ
    connection = await aio_pika.connect_robust(settings.rabbitmq.url)
    channel = await connection.channel()
    queue = await channel.declare_queue(
        settings.MESSAGE_QUEUE_NAME,
        durable=True,
    )

    # Start consuming messages
    await queue.consume(
        lambda message: process_message(message, batcher),
    )

    print(" [*] Waiting for messages. To exit press CTRL+C")
    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
