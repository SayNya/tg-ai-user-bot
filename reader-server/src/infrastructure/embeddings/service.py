import numpy as np
import onnxruntime as ort
from scipy.spatial.distance import cdist
from tokenizers import Tokenizer

from src.core import settings
from src.domain import Topic
from src.infrastructure import get_topic_repository


class SentenceTransformerService:
    def __init__(self) -> None:
        self.tokenizer = Tokenizer.from_file(
            str(settings.ai_model_dir / "tokenizer.json"),
        )
        self.session = ort.InferenceSession(
            str(settings.ai_model_dir / "model.onnx"),
        )

        self.input_name = self.session.get_inputs()[0].name
        self.attn_name = self.session.get_inputs()[1].name
        self.output_name = self.session.get_outputs()[0].name

        self.cache: dict[tuple, dict] = {}

    async def get_topic_embeddings(
        self,
        user_id: str,
        chat_id: str,
    ) -> dict[int, tuple[str, np.ndarray, Topic]]:
        key = (user_id, chat_id)
        if key in self.cache:
            return self.cache[key]

        topics = await self.get_topics_from_db(user_id, chat_id)

        topic_data = {t.id: f"{t.name} {t.description}" for t in topics}
        texts = list(topic_data.values())
        embs = self.encode(texts)

        cache = dict(zip(topic_data.keys(), zip(texts, embs, topics)))
        self.cache[key] = cache
        return cache

    def encode(self, texts: list[str]) -> np.ndarray:
        input_ids, attention_mask = self._tokenize(texts)

        outputs = self.session.run(
            [self.output_name],
            {
                self.input_name: input_ids,
                self.attn_name: attention_mask,
            },
        )[0]  # (batch_size, seq_len, hidden_size)

        # mean pooling
        return (outputs * np.expand_dims(attention_mask, axis=-1)).sum(
            axis=1,
        ) / attention_mask.sum(axis=1, keepdims=True)

    async def encode_messages(self, messages: list[str]) -> np.ndarray:
        return self.encode(messages)

    @staticmethod
    async def compute_similarity(
        message_embeddings: np.ndarray,
        topic_embeddings: np.ndarray,
    ) -> np.ndarray:
        # Вычисляем cos_sim с помощью scipy (или вручную)
        return 1 - cdist(message_embeddings, topic_embeddings, metric="cosine")

    def _tokenize(self, texts: list[str]) -> tuple[np.ndarray, np.ndarray]:
        tokens = self.tokenizer.encode_batch(texts)
        max_len = max(len(t.ids) for t in tokens)

        input_ids = np.zeros((len(tokens), max_len), dtype=np.int64)
        attn_mask = np.zeros((len(tokens), max_len), dtype=np.int64)

        for i, t in enumerate(tokens):
            input_ids[i, : len(t.ids)] = t.ids
            attn_mask[i, : len(t.attention_mask)] = t.attention_mask

        return input_ids, attn_mask

    @staticmethod
    async def get_topics_from_db(
        user_id: str,
        chat_id: str,
    ) -> list[Topic] | None:
        async with get_topic_repository() as topic_repo:
            return await topic_repo.get_chat_topics(user_id, chat_id)
