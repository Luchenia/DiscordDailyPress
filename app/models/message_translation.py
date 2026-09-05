from datetime import UTC
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class MessageTranslation(Base):
    """Regenerable translation derived from a specific message content."""

    __tablename__ = "message_translations"

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "target_language",
            "source_content_hash",
            name="uq_message_translation_message_target_hash",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        nullable=False,
        index=True,
    )

    source_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    target_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    source_content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    translated_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
