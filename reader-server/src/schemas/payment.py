from pydantic import BaseModel


class PaymentCallback(BaseModel):
    user_id: int
    payment_id: str
    amount: float
    status: str
