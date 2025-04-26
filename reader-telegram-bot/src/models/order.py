from pydantic import BaseModel


class OrderModel(BaseModel):
    id: int
    uuid: str
    is_paid: bool
    user_id: int
    amount: float
