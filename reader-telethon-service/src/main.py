import asyncio
import signal

import anyio

from src.config import Container, settings


async def start_consumers(container: Container) -> None:
    registration_consumer = container.registration_consumer()
    message_consumer = container.message_consumer()
    client_consumer = container.client_consumer()

    await registration_consumer.connect()
    await message_consumer.connect()
    await client_consumer.connect()


async def shutdown(container: Container) -> None:
    await container.client_manager().stop_all_clients()

    await container.registration_consumer().close()
    await container.message_consumer().close()
    await container.client_consumer().close()

    for hook in container.shutdown_hooks():
        await hook()


async def main() -> None:
    container = Container()
    container.config.from_pydantic(settings)

    await start_consumers(container)

    await container.client_manager().start_all_clients()

    watchdog_task = asyncio.create_task(container.watchdog().start())

    shutdown_event = anyio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown_event.set()),
        )

    try:
        await shutdown_event.wait()
    finally:
        watchdog_task.cancel()
        await shutdown(container)


if __name__ == "__main__":
    asyncio.run(main())
