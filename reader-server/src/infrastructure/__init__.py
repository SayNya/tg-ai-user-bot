"""
Infrastructure module containing external service integrations and implementations.
"""

from .database import (
    Base,
    Chat,
    ChatTopic,
    SQLAlchemyMessageRepository,
    SQLAlchemyTopicRepository,
    Topic,
    User,
    db_manager,
    get_message_repository,
    get_topic_repository,
)
from .embeddings import SentenceTransformerService
from .messaging import AnswerTaskPublisher

__all__ = [
    "AnswerTaskPublisher",
    "Base",
    "Chat",
    "ChatTopic",
    "SQLAlchemyMessageRepository",
    "SQLAlchemyTopicRepository",
    "SentenceTransformerService",
    "Topic",
    "User",
    "db_manager",
    "get_message_repository",
    "get_topic_repository",
]
