from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.message import Message
from datetime import datetime




class MessageRepository:
    """
    Message 테이블 전담 Repository
    """

    def save(self, message: Message) -> Message:
        with SessionLocal() as session:
            session.add(message)
            session.commit()
            session.refresh(message)

            return message

    def get_all(self) -> list[Message]:
        with SessionLocal() as session:
            result = session.scalars(
                select(Message)
            )

            return list(result)

        
    def get_by_id(self, message_id: int) -> Message | None:
        with SessionLocal() as session:
            return session.get(Message, message_id)


    def count(self) -> int:
        with SessionLocal() as session:
            return session.scalar(
                select(func.count()).select_from(Message)
            )


    def delete_by_id(self, message_id: int) -> bool:
        with SessionLocal() as session:

            message = session.get(Message, message_id)

            if message is None:
                return False

            session.delete(message)
            session.commit()

            return True
        
    def update(
        self,
        message: Message,
    ) -> Message:

        with SessionLocal() as session:

            merged = session.merge(message)

            session.commit()

            session.refresh(merged)

            return merged

    def get_by_discord_message_id(
        self,
        discord_message_id: int,
    ) -> Message | None:

        with SessionLocal() as session:

            return session.scalar(
                select(Message).where(
                    Message.discord_message_id == discord_message_id
                )
            )

    def update_language(
        self,
        discord_message_id: int,
        language: str,
    ) -> bool:

        with SessionLocal() as session:

            message = session.scalar(
                select(Message).where(
                    Message.discord_message_id == discord_message_id
                )
            )

            if message is None:
                return False

            message.language = language

            session.commit()

            return True

    def get_by_analysis_scope(
        self,
        guild_id: int,
        channel_ids: list[int],
        start_at: datetime,
        end_at: datetime,
    ) -> list[Message]:

        with SessionLocal() as session:

            result = session.scalars(
                select(Message).where(
                    Message.guild_id == guild_id,
                    Message.channel_id.in_(channel_ids),
                    Message.created_at >= start_at,
                    Message.created_at < end_at,
                )
            )

            return list(result)