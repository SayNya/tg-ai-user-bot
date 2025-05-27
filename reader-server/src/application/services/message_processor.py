from collections import defaultdict

from src.core import settings
from src.domain import AnswerTask, Message
from src.infrastructure import AnswerTaskPublisher, SentenceTransformerService


class MessageProcessor:
    def __init__(
        self,
        embedding_service: SentenceTransformerService,
        publisher: AnswerTaskPublisher,
    ) -> None:
        self.embedding_service = embedding_service
        self.publisher = publisher

    async def process_messages(self, batch: list[Message]) -> None:
        grouped: dict[tuple[int, int], list[Message]] = defaultdict(list)
        for msg in batch:
            grouped[msg.user_id, msg.chat_id].append(msg)

        for (user_id, chat_id), messages in grouped.items():
            # Get topic embeddings
            topic_embs = await self.embedding_service.get_topic_embeddings(
                user_id,
                chat_id,
            )

            # Prepare data
            topic_ids = list(topic_embs.keys())
            topic_torch_embs = [topic_embs[tid][1] for tid in topic_ids]
            topic_objs = [topic_embs[tid][2] for tid in topic_ids]

            # Process messages
            message_texts = [msg.message_text for msg in messages]
            message_embs = await self.embedding_service.encode_messages(message_texts)

            # Compute similarities
            cosine_scores = await self.embedding_service.compute_similarity(
                message_embs,
                topic_torch_embs,
            )
            max_scores, max_indices = cosine_scores.max(dim=1)

            # Process matches
            for i, (score, idx) in enumerate(zip(max_scores, max_indices)):
                confidence_score = score.item()
                if confidence_score >= settings.SIMILARITY_THRESHOLD:
                    msg = batch[i]
                    matched_topic = topic_objs[idx]
                    task = AnswerTask(
                        user_id=user_id,
                        chat_id=chat_id,
                        telegram_message_id=msg.telegram_message_id,
                        content=msg.message_text,
                        topic_id=matched_topic.id,
                        score=confidence_score,
                        sender_username=msg.sender_username,
                    )
                    await self.publisher.send(task)
