from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class Message(Base):
    """
    Discord 메시지
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True
    )

    author_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True
    )

    author_name: Mapped[str] = mapped_column(
        String(100)
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="unknown"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )