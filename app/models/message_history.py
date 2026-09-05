from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class MessageHistory(Base):
    """
    메시지 수정 이력
    """

    __tablename__ = "message_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # 우리 DB의 Message PK
    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        index=True,
    )

    # Discord 원본 ID
    discord_message_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    # 몇 번째 수정인가
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    # 수정 전
    old_content: Mapped[str] = mapped_column(
        Text,
    )

    # 수정 후
    new_content: Mapped[str] = mapped_column(
        Text,
    )

    # 수정 시각
    edited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    edit_reason: Mapped[str | None]
