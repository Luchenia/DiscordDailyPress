from sqlalchemy import select

from app.database.session import SessionLocal
from app.models.collection_channel import CollectionChannel


class CollectionChannelRepository:
    """
    분석 대상 CollectionChannel 테이블 담당 Repository
    """

    def add(
        self,
        channel: CollectionChannel,
    ) -> CollectionChannel:

        with SessionLocal() as session:
            session.add(channel)
            session.commit()
            session.refresh(channel)

            return channel

    def get_by_guild(
        self,
        guild_id: int,
    ) -> list[CollectionChannel]:

        with SessionLocal() as session:
            result = session.scalars(
                select(CollectionChannel).where(
                    CollectionChannel.guild_id == guild_id
                )
            )

            return list(result)

    def get_enabled_channel_ids(
        self,
        guild_id: int,
    ) -> list[int]:

        with SessionLocal() as session:
            result = session.scalars(
                select(CollectionChannel.channel_id)
                .where(
                    CollectionChannel.guild_id == guild_id,
                    CollectionChannel.enabled.is_(True),
                )
                .order_by(
                    CollectionChannel.channel_id
                )
            )

            return list(result)

    def disable(
        self,
        guild_id: int,
        channel_id: int,
    ) -> bool:

        with SessionLocal() as session:

            channel = session.scalar(
                select(CollectionChannel).where(
                    CollectionChannel.guild_id == guild_id,
                    CollectionChannel.channel_id == channel_id,
                )
            )

            if channel is None:
                return False

            channel.enabled = False

            session.commit()

            return True

    def enable(
        self,
        guild_id: int,
        channel_id: int,
    ) -> bool:

        with SessionLocal() as session:

            channel = session.scalar(
                select(CollectionChannel).where(
                    CollectionChannel.guild_id == guild_id,
                    CollectionChannel.channel_id == channel_id,
                )
            )

            if channel is None:
                return False

            channel.enabled = True

            session.commit()

            return True
