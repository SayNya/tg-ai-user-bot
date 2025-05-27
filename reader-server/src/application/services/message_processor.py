from collections import defaultdict

import structlog

from src.core import settings
from src.domain import AnswerTask, Message
from src.infrastructure import AnswerTaskPublisher, SentenceTransformerService


class MessageProcessor:
    def __init__(
        self,
        embedding_service: SentenceTransformerService,
        publisher: AnswerTaskPublisher,
        logger: structlog.typing.FilteringBoundLogger,
    ) -> None:
        self.embedding_service = embedding_service
        self.publisher = publisher
        self.logger = logger

    async def process_messages(self, batch: list[Message]) -> None:
        self.logger.info("starting_message_processing", batch_size=len(batch))

        grouped: dict[tuple[int, int], list[Message]] = defaultdict(list)
        for msg in batch:
            grouped[msg.user_id, msg.chat_id].append(msg)

        self.logger.info("messages_grouped", num_groups=len(grouped))

        for (user_id, chat_id), messages in grouped.items():
            self.logger.info(
                "processing_user_chat_messages",
                user_id=user_id,
                chat_id=chat_id,
                message_count=len(messages),
            )

            topic_embs = await self.embedding_service.get_topic_embeddings(
                user_id,
                chat_id,
            )
            self.logger.info("retrieved_topic_embeddings", num_topics=len(topic_embs))

            topic_ids = list(topic_embs.keys())
            topic_torch_embs = [topic_embs[tid][1] for tid in topic_ids]
            topic_objs = [topic_embs[tid][2] for tid in topic_ids]

            message_texts = [msg.message_text for msg in messages]
            message_embs = await self.embedding_service.encode_messages(message_texts)
            self.logger.info("encoded_messages", num_messages=len(message_embs))

            cosine_scores = await self.embedding_service.compute_similarity(
                message_embs,
                topic_torch_embs,
            )
            max_scores, max_indices = cosine_scores.max(dim=1)

            tasks_published = 0
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
                    tasks_published += 1
                    self.logger.info(
                        "published_answer_task",
                        user_id=user_id,
                        chat_id=chat_id,
                        message_id=msg.telegram_message_id,
                        topic_id=matched_topic.id,
                        confidence_score=confidence_score,
                    )

            self.logger.info(
                "finished_processing_user_chat",
                user_id=user_id,
                chat_id=chat_id,
                tasks_published=tasks_published,
            )

        self.logger.info("completed_message_processing", total_messages=len(batch))
