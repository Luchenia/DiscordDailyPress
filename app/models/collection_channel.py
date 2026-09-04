from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class CollectionChannel(Base):
    """
    Chronicle이 분석 대상으로 관리하는 Discord 채널.

    활성화 상태는 분석 범위만 결정한다. 길드 원본 메시지 수집은
    이 설정과 독립적으로 수행된다.
    """

    __tablename__ = "collection_channels"

    __table_args__ = (
        UniqueConstraint(
            "guild_id",
            "channel_id",
            name="uq_collection_channel_guild_channel",
        ),
    )

    # ==========================
    # 내부 PK
    # ==========================
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # ==========================
    # Discord 서버 정보
    # ==========================
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    # ==========================
    # Discord 채널 정보
    # ==========================
    channel_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
    )

    channel_name: Mapped[str] = mapped_column(
        String(150),
    )

    # ==========================
    # 분석 포함 여부
    # ==========================
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )
