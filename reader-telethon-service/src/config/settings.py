from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    name: str = "name"
    username: str = "username"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432
    url: str = ""

    def model_post_init(self, *args, **kwargs) -> None:
        self.url = f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class RabbitMQSettings(BaseModel):
    url: str = "amqp://guest:guest@localhost/"


class OpenAISettings(BaseModel):
    api_key: str = "sk-proj-1234567890"
    proxy: str = "http://localhost:8080"


class Settings(BaseSettings):
    debug: bool = True

    root_dir: Path
    src_dir: Path

    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    openai: OpenAISettings = OpenAISettings()
    model_config = SettingsConfigDict(env_file=".env")


ROOT_PATH = Path(__file__).parent.parent.parent
SOURCE_PATH = ROOT_PATH / "src"

settings = Settings(root_dir=ROOT_PATH, src_dir=SOURCE_PATH)
