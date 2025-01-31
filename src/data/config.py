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

FSM_HOST: str = env.str("FSM_HOST")
FSM_PORT: int = env.int("FSM_PORT")
FSM_PASSWORD: str = env.str("FSM_PASSWORD")

CHAT_GPT_API = env.str("CHAT_GPT_API")
CHAT_GPT_ASSISTANT_CHECK = env.str("CHAT_GPT_ASSISTANT_CHECK")
CHAT_GPT_ASSISTANT_MESSAGE = env.str("CHAT_GPT_ASSISTANT_MESSAGE")


PROJECT_DIR: Path = Path(__file__).parent.parent.parent
SOURCE_DIR: Path = PROJECT_DIR / "src"
SESSIONS_DIR: Path = SOURCE_DIR / "data" / "sessions"

PROXY = env.str("PROXY")
