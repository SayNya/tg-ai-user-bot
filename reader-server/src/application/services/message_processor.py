import datetime
import json
import uuid
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

import numpy as np
import structlog

from src.core import settings
from src.domain import AnswerTask, Message, Topic
from src.infrastructure import AnswerTaskPublisher, SentenceTransformerService


class TopicEmbedding(TypedDict):
    text: str
    embedding: np.ndarray
    topic: Topic


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
        """Process a batch of messages, matching them to relevant topics."""
        self.logger.info("starting_message_processing", batch_size=len(batch))

        # Group messages by user and chat
        grouped_messages = self._group_messages_by_user_chat(batch)
        self.logger.info("messages_grouped", num_groups=len(grouped_messages))

        for (user_id, chat_id), messages in grouped_messages.items():
            await self._process_user_chat_messages(user_id, chat_id, messages)

        self.logger.info("completed_message_processing", total_messages=len(batch))

    @staticmethod
    def _group_messages_by_user_chat(
        batch: list[Message],
    ) -> dict[tuple[int, int], list[Message]]:
        """Group messages by user_id and chat_id."""
        grouped: dict[tuple[int, int], list[Message]] = defaultdict(list)
        for msg in batch:
            grouped[msg.user_id, msg.chat_id].append(msg)
        return grouped

    async def _process_user_chat_messages(
        self,
        user_id: int,
        chat_id: int,
        messages: list[Message],
    ) -> None:
        """Process messages for a specific user and chat."""
        self.logger.info(
            "processing_user_chat_messages",
            user_id=user_id,
            chat_id=chat_id,
            message_count=len(messages),
        )

        # Get topic embeddings
        topic_embeddings = await self.embedding_service.get_topic_embeddings(
            user_id,
            chat_id,
        )
        self.logger.info("retrieved_topic_embeddings", num_topics=len(topic_embeddings))

        if not topic_embeddings:
            return

        # Prepare topic data
        topic_data = self._prepare_topic_data(topic_embeddings)

        # Process messages
        message_texts = [msg.text for msg in messages]
        message_embeddings = await self.embedding_service.encode_messages(message_texts)
        self.logger.info("encoded_messages", num_messages=len(message_embeddings))

        # Compute similarities and find matches
        similarity_scores = await self.embedding_service.compute_similarity(
            message_embeddings,
            topic_data["embeddings"],
        )
        self._save_debug_similarity(
            user_id,
            chat_id,
            messages,
            similarity_scores,
            topic_data,
        )
        # Get best matches using vectorized operations
        max_indices = np.argmax(similarity_scores, axis=1)
        max_scores = similarity_scores[np.arange(len(similarity_scores)), max_indices]

        # Process matches and publish tasks
        await self._publish_matching_tasks(
            user_id,
            chat_id,
            messages,
            max_scores,
            max_indices,
            topic_data,
        )

    def _save_debug_similarity(
        self,
        user_id: int,
        chat_id: int,
        messages: list[Message],
        similarity_scores: np.ndarray,
        topic_data: dict[str, list],
    ) -> None:
        """Сохраняет similarity-оценки для отладки в JSON-файл."""

        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        unique_id = uuid.uuid4().hex[:8]

        # Путь до директории
        debug_dir = Path(settings.src_dir) / "ai_model" / "similarity_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)

        # Путь до файла
        filename = debug_dir / f"{user_id}_{chat_id}_{timestamp}_{unique_id}.json"

        debug_data = []

        for i, message in enumerate(messages):
            message_result = {
                "message_id": message.telegram_message_id,
                "message_text": message.text,
                "similarities": [],
            }

            for j, topic in enumerate(topic_data["topics"]):
                message_result["similarities"].append({
                    "topic_id": topic.id,
                    "topic_title": topic.title,
                    "topic_description": topic.description,
                    "score": float(similarity_scores[i][j]),
                })

            debug_data.append(message_result)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        self.logger.info(
            "similarity_debug_saved",
            file_path=str(filename),
            messages=len(messages),
            topics=len(topic_data["topics"]),
        )

    @staticmethod
    def _prepare_topic_data(
        topic_embeddings: dict[int, tuple[str, np.ndarray, Topic]],
    ) -> dict[str, list]:
        """Prepare topic data for processing."""
        topic_ids = list(topic_embeddings.keys())
        return {
            "ids": topic_ids,
            "embeddings": [topic_embeddings[tid][1] for tid in topic_ids],
            "topics": [topic_embeddings[tid][2] for tid in topic_ids],
        }

    async def _publish_matching_tasks(
        self,
        user_id: int,
        chat_id: int,
        messages: list[Message],
        scores: np.ndarray,
        indices: np.ndarray,
        topic_data: dict[str, list],
    ) -> None:
        """Publish tasks for messages that match topics above threshold."""
        tasks_published = 0
        for i, (score, idx) in enumerate(zip(scores, indices)):
            if score >= settings.SIMILARITY_THRESHOLD:
                msg = messages[i]
                matched_topic = topic_data["topics"][idx]

                task = AnswerTask(
                    telegram_message_id=msg.telegram_message_id,
                    user_id=user_id,
                    chat_id=chat_id,
                    text=msg.text,
                    sender_username=msg.sender_username,
                    sender_id=msg.sender_id,
                    created_at=msg.created_at,
                    topic_id=matched_topic.id,
                    score=float(score),  # Convert numpy float to Python float
                )
                print(task)

                await self.publisher.send(task)
                tasks_published += 1

                self.logger.info(
                    "published_answer_task",
                    user_id=user_id,
                    chat_id=chat_id,
                    message_id=msg.telegram_message_id,
                    topic_id=matched_topic.id,
                    confidence_score=float(score),
                )

        self.logger.info(
            "finished_processing_user_chat",
            user_id=user_id,
            chat_id=chat_id,
            tasks_published=tasks_published,
        )
