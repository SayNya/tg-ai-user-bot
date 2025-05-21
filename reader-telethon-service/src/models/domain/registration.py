from pydantic import BaseModel


class RegistrationInit(BaseModel):
    user_id: int
    phone: str
    api_id: int
    api_hash: str


class RegistrationConfirm(BaseModel):
    user_id: int
    code: str


class RegistrationPasswordConfirm(BaseModel):
    user_id: int
    password: str


class AuthData(BaseModel):
    user_id: int
    phone: str
    api_id: int
    api_hash: str
    phone_code_hash: str
