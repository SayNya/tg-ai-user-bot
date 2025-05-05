from src.schemas.payment import PaymentCallback
from src.services.rabbitmq import rabbitmq_client
from fastapi import APIRouter

router = APIRouter()


@router.post("/payment/callback")
async def payment_callback(data: PaymentCallback) -> dict:
    if data.status == "success":
        text = f"Оплата {data.amount}₽ прошла успешно!"
    else:
        text = f"Оплата {data.amount}₽ не удалась."

    await rabbitmq_client.publish(
        routing_key="payment_notifications",
        message_body=f"{data.user_id}|{text}".encode(),
    )

    return {"status": "ok"}
