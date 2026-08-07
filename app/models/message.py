from datetime import UTC
from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class Message(Base):
    """
    Discord 메시지

    AI 신문사의 가장 기본이 되는 원본 데이터
    """

    __tablename__ = "messages"

    # ==========================
    # 내부 PK
    # ==========================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # ==========================
    # Discord 원본 정보
    # ==========================
    discord_message_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    guild_name: Mapped[str] = mapped_column(
        String(150),
    )

    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    channel_name: Mapped[str] = mapped_column(
        String(150),
    )

    # ==========================
    # 작성자 정보
    # ==========================
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    author_username: Mapped[str] = mapped_column(
        String(100),
    )

    author_display_name: Mapped[str] = mapped_column(
        String(100),
    )

    is_bot: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    # ==========================
    # 메시지 내용
    # ==========================
    content: Mapped[str] = mapped_column(
        Text,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="unknown",
    )

    # ==========================
    # 첨부파일
    # ==========================
    has_attachment: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    attachment_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # ==========================
    # 답글 정보
    # ==========================
    reply_to_message_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    # ==========================
    # 시간 정보
    # ==========================
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )