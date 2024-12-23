from pyrogram import Client

from src.data import config

app = Client(
    name=config.LOGIN,
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    phone_number=config.PHONE,
    workdir=str(config.SESSIONS_DIR),
)
