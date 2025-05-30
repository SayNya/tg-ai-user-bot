import datetime
from typing import Optional, TypeVar

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


ConcreteTable = TypeVar("ConcreteTable", bound=Base)


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(primary_key=True)
    host: Mapped[str] = mapped_column(String(32), nullable=False)
    port: Mapped[int] = mapped_column(nullable=False)
    username: Mapped[str | None] = mapped_column(Text, nullable=True)
    password: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    users: Mapped[list["User"]] = relationship(back_populates="proxy")

    def __repr__(self) -> str:
        return f"<Proxy(id={self.id}, host={self.host}, port={self.port})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    is_bot: Mapped[bool] = mapped_column(default=False, nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)

    last_name: Mapped[str] = mapped_column(String(128), nullable=True)
    username: Mapped[str] = mapped_column(String(32), nullable=True)
    language_code: Mapped[str] = mapped_column(String(16), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    proxy_id: Mapped[int | None] = mapped_column(
        ForeignKey("proxies.id"),
        nullable=True,
    )
    proxy: Mapped[Optional["Proxy"]] = relationship(back_populates="users")

    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    topics: Mapped[list["Topic"]] = relationship(back_populates="user")
    auth: Mapped["TelegramAuth"] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class TelegramAuth(Base):
    __tablename__ = "telegram_auth"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    api_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    session_string: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    user = relationship("User", back_populates="auth")

    def __repr__(self) -> str:
        return (
            f"<TelegramAuth(id={self.id}, user_id={self.user_id}, phone={self.phone})>"
        )


class Chat(Base):
    __tablename__ = "chats"
    __table_args__ = (
        UniqueConstraint("telegram_chat_id", "user_id", name="uix_chat_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="chats")

    topics: Mapped[list["ChatTopic"]] = relationship(back_populates="chat")
    threads: Mapped[list["Thread"]] = relationship(back_populates="chat")

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, telegram_chat_id={self.telegram_chat_id}, name={self.name})>"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="topics")

    chats: Mapped[list["ChatTopic"]] = relationship(back_populates="topic")
    threads: Mapped[list["Thread"]] = relationship(back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, name={self.name})>"


class ChatTopic(Base):
    __tablename__ = "chat_topics"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"),
        primary_key=True,
    )

    chat: Mapped["Chat"] = relationship(back_populates="topics")
    topic: Mapped["Topic"] = relationship(back_populates="chats")

    def __repr__(self) -> str:
        return f"<ChatTopic(chat_id={self.chat_id}, topic_id={self.topic_id})>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    confidence_score: Mapped[float | None] = mapped_column(nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    parent_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent: Mapped[Optional["Message"]] = relationship(remote_side="Message.id")

    thread_id: Mapped[int | None] = mapped_column(
        ForeignKey("threads.id", ondelete="SET NULL"),
    )
    thread: Mapped[Optional["Thread"]] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, telegram_message_id={self.telegram_message_id})>"
        )


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(primary_key=True)

    initiator_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    initiator_username: Mapped[str | None] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chat: Mapped["Chat"] = relationship(back_populates="threads")

    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic: Mapped[Optional["Topic"]] = relationship(back_populates="threads")

    messages: Mapped[list["Message"]] = relationship(back_populates="thread")

    def __repr__(self) -> str:
        return f"<Thread(id={self.id}, chat_id={self.chat_id})>"
