from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseModel):
    token: str = "12345:abc123"

    @property
    def id(self) -> int:
        return int(self.token.split(":")[0])


class DatabaseSettings(BaseModel):
    name: str = "name"
    username: str = "username"
    password: str = "password"
    host: str = "host"
    port: int = 543253424523432423

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"


class ModulbankSettings(BaseModel):
    host: str = "localhost"
    merchant_id: str = "123"
    secret: str = "abc213"


class DeepseekSettings(BaseModel):
    api_key: str = "abc123"


class RabbitMQSettings(BaseModel):
    url: str = "amqp://guest:guest@localhost/"


class CacheSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 1


class StorageSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 2


class Settings(BaseSettings):
    debug: bool = True

    use_cache: bool = True

    root_dir: Path
    src_dir: Path

    database: DatabaseSettings = DatabaseSettings()
    bot: BotSettings = BotSettings()
    modulbank: ModulbankSettings = ModulbankSettings()
    deepseek: DeepseekSettings = DeepseekSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    cache: CacheSettings = CacheSettings()
    storage: StorageSettings = StorageSettings()

    model_config = SettingsConfigDict(env_file=".env")


ROOT_PATH = Path(__file__).parent.parent.parent
SOURCE_PATH = ROOT_PATH / "src"

print("Root path:", ROOT_PATH)
print("Looking for .env file in:", ROOT_PATH / ".env")
print("Current working directory:", Path.cwd())

settings = Settings(root_dir=ROOT_PATH, src_dir=SOURCE_PATH)
print("Database settings:", settings.database.model_dump())
print("Database port:", settings.database.port)
print("Database URL:", settings.database.url)
