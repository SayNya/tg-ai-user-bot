import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


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

    chats: Mapped[list["Chat"]] = relationship(back_populates="user")
    topics: Mapped[list["Topic"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_user_id={self.telegram_user_id}, username={self.username})>"


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

    chat_topics: Mapped[list["ChatTopic"]] = relationship(back_populates="chat")

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, telegram_chat_id={self.telegram_chat_id}, title={self.title})>"


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    prompt: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.now)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship(back_populates="topics")

    chat_topics: Mapped[list["ChatTopic"]] = relationship(back_populates="topic")

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

    chat: Mapped["Chat"] = relationship(back_populates="chat_topics")
    topic: Mapped["Topic"] = relationship(back_populates="chat_topics")

    def __repr__(self) -> str:
        return f"<ChatTopic(chat_id={self.chat_id}, topic_id={self.topic_id})>"
