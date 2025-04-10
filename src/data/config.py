from pathlib import Path

from environs import Env

env = Env()
env.read_env()

BOT_TOKEN: str = env.str("BOT_TOKEN")
BOT_ID: str = BOT_TOKEN.split(":")[0]

DEBUG: bool = env.bool("DEBUG", False)

PG_HOST: str = env.str("PG_HOST")
PG_PORT: int = env.int("PG_PORT")
PG_USER: str = env.str("PG_USER")
PG_PASSWORD: str = env.str("PG_PASSWORD")
PG_DATABASE: str = env.str("PG_DATABASE")

CHAT_GPT_API = env.str("CHAT_GPT_API")
CHAT_GPT_ASSISTANT_CHECK = env.str("CHAT_GPT_ASSISTANT_CHECK")
CHAT_GPT_ASSISTANT_MESSAGE = env.str("CHAT_GPT_ASSISTANT_MESSAGE")


PROXY = env.str("PROXY")

PROJECT_DIR: Path = Path(__file__).parent.parent.parent
SOURCE_DIR: Path = PROJECT_DIR / "src"
SESSIONS_DIR: Path = SOURCE_DIR / "data" / "sessions"

MODULBANK_HOST: str = "https://app.alfaseller.pro"
MODULBANK_MERCHANT_ID: str = "ba68d804-0ced-4ed3-b059-432392794253"
MODULBANK_SECRET: str = env.str("MODULBANK_SECRET", "110F9C03A3BAC0971E9F0DD2047DC6B1")
