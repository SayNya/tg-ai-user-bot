from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    name: str = "name"
    username: str = "username"
    password: str = "password"
    host: str = "localhost"
    port: int = 5432

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class RabbitMQSettings(BaseModel):
    url: str = "amqp://guest:guest@localhost/"


class Settings(BaseSettings):
    debug: bool = True

    root_dir: Path
    src_dir: Path

    ANSWER_QUEUE_NAME: str = "message.answer"
    MESSAGE_QUEUE_NAME: str = "message.process"
    BATCH_SIZE: int = 20
    BATCH_TIME: int = 60
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    SIMILARITY_THRESHOLD: float = 0.5

    database: DatabaseSettings = DatabaseSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()

    model_config = SettingsConfigDict(env_file=".env")


ROOT_PATH = Path(__file__).parent.parent.parent
SOURCE_PATH = ROOT_PATH / "src"

settings = Settings(root_dir=ROOT_PATH, src_dir=SOURCE_PATH)
