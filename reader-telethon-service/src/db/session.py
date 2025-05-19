import json

import orjson
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    url=settings.database.url,
    json_serializer=json.dumps,
    json_deserializer=orjson.loads,
    echo=(bool(settings.debug)),
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
