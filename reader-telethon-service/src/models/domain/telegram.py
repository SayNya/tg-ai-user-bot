from pydantic import BaseModel


class AuthModel(BaseModel):
    user_id: int
    api_id: int
    api_hash: str
    session_string: str
