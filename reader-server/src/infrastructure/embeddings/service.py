import torch
from sentence_transformers import SentenceTransformer, util

from src.core import settings
from src.domain import Topic
from src.infrastructure import get_topic_repository


class SentenceTransformerService:
    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.cache: dict[tuple, dict] = {}

    async def get_topic_embeddings(
        self,
        user_id: str,
        chat_id: str,
    ) -> dict[int, tuple[str, torch.Tensor, Topic]]:
        key = (user_id, chat_id)
        if key in self.cache:
            return self.cache[key]

        topics = await self.get_topics_from_db(user_id, chat_id)

        topic_data = {t.id: f"{t.name} {t.description}" for t in topics}
        texts = list(topic_data.values())
        embs = self.model.encode(texts, convert_to_tensor=True)

        cache = dict(zip(topic_data.keys(), zip(texts, embs, topics)))
        self.cache[key] = cache
        return cache

    async def encode_messages(self, messages: list[str]) -> torch.Tensor:
        return self.model.encode(messages, convert_to_tensor=True)

    @staticmethod
    async def compute_similarity(
        message_embeddings: torch.Tensor,
        topic_embeddings: torch.Tensor,
    ) -> torch.Tensor:
        return util.cos_sim(message_embeddings, topic_embeddings)

    @staticmethod
    async def get_topics_from_db(
        user_id: str,
        chat_id: str,
    ) -> list[Topic] | None:
        async with get_topic_repository() as topic_repo:
            return await topic_repo.get_chat_topics(user_id, chat_id)
