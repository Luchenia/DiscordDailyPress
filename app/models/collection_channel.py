from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class CollectionChannel(Base):
    """
    Chronicle이 수집 대상으로 관리하는 Discord 채널
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
    # 수집 활성화 여부
    # ==========================
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )