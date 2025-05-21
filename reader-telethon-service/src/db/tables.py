import datetime
from typing import Optional, TypeVar

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.models.enums import SenderType


class Base(AsyncAttrs, DeclarativeBase):
    pass


ConcreteTable = TypeVar("ConcreteTable", bound=Base)


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[int] = mapped_column(primary_key=True)
    host: Mapped[str] = mapped_column(String(32), nullable=False)
    port: Mapped[int] = mapped_column(nullable=False)
    username: Mapped[str | None] = mapped_column(Text)
    password: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    users: Mapped[list["User"]] = relationship(back_populates="proxy")

    def __repr__(self) -> str:
        return f"<Proxy(id={self.id}, host={self.host}, port={self.port})>"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(32))
    is_bot: Mapped[bool] = mapped_column(default=False, nullable=False)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False)
    last_name: Mapped[str] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str] = mapped_column(String(16))

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    proxy_id: Mapped[int | None] = mapped_column(ForeignKey("proxies.id"))
    proxy: Mapped[Optional["Proxy"]] = relationship(back_populates="users")

    auth: Mapped["TelegramAuth"] = relationship(back_populates="user")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    topics: Mapped[list["Topic"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_user_id={self.telegram_user_id}, username={self.username})>"


class TelegramAuth(Base):
    __tablename__ = "telegram_auth"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    api_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    session_string: Mapped[str] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
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
    title: Mapped[str | None] = mapped_column(String(256))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="chats")

    messages: Mapped[list["Message"]] = relationship(back_populates="chat")

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, telegram_chat_id={self.telegram_chat_id}, title={self.title})>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sender_type: Mapped[SenderType] = mapped_column(Enum(SenderType), nullable=False)
    sender_username: Mapped[str] = mapped_column(String(32), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    chat: Mapped["Chat"] = relationship(back_populates="messages")

    topic_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic: Mapped[Optional["Topic"]] = relationship(back_populates="messages")

    parent_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent: Mapped[Optional["Message"]] = relationship(remote_side="Message.id")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender={self.sender}, telegram_message_id={self.telegram_message_id})>"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="topics")

    messages: Mapped[list["Message"]] = relationship(back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, name={self.name})>"
