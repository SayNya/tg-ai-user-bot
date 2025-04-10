from .base import BaseModel


class UserModel(BaseModel):
    id: int


class PaymentData(UserModel):
    balance: float
    is_subscribed: bool
