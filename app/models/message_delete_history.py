from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class MessageDeleteHistory(Base):
    """
    삭제된 메시지 이력
    """

    __tablename__ = "message_delete_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 우리 DB PK
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        index=True,
    )

    # Discord 원본 ID
    discord_message_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    guild_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    author_id: Mapped[int] = mapped_column(
        BigInteger,
    )

    author_display_name: Mapped[str] = mapped_column(
        String(100),
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
