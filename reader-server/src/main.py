from fastapi import FastAPI
from src.api.routes import payment
from src.services.rabbitmq import rabbitmq_client
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ANN201, ARG001
    await rabbitmq_client.connect()
    yield
    await rabbitmq_client.close()


app = FastAPI(title="FastAPI Payment Service")

app.include_router(payment.router, prefix="/api/v1")
