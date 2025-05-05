from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq/"
    project_name: str = "FastAPI Payment Service"
    api_v1_prefix: str = "/api/v1"


settings = Settings()
