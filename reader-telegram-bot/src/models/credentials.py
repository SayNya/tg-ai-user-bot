from .base import BaseModel


class CredentialsModel(BaseModel):
    id: int
    api_id: int
    api_hash: str
    phone: str
    user_id: int | None
