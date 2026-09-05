from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.message import Message
from app.utils.datetime_utils import ensure_utc


@dataclass(frozen=True)
class MessageSaveResult:
    message: Message
    created: bool




class MessageRepository:
    """
    Message 테이블 전담 Repository
    """

    def save(self, message: Message) -> MessageSaveResult:
        with SessionLocal() as session:
            try:
                session.add(message)
                session.commit()
                session.refresh(message)

                return MessageSaveResult(
                    message=message,
                    created=True,
                )

            except IntegrityError:
                session.rollback()

                existing = session.scalar(
                    select(Message).where(
                        Message.discord_message_id
                        == message.discord_message_id
                    )
                )

                if existing is None:
                    raise

                return MessageSaveResult(
                    message=existing,
                    created=False,
                )

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


    def soft_delete_by_id(
        self,
        message_id: int,
        deleted_at: datetime,
        session: Session | None = None,
    ) -> bool:
        if session is not None:
            return self._soft_delete_by_id(
                session,
                message_id,
                deleted_at,
            )

        with SessionLocal() as session:
            deleted = self._soft_delete_by_id(
                session,
                message_id,
                deleted_at,
            )
            session.commit()

            return deleted

    @staticmethod
    def _soft_delete_by_id(
        session: Session,
        message_id: int,
        deleted_at: datetime,
    ) -> bool:
        message = session.get(Message, message_id)

        if message is None:
            return False

        if message.deleted_at is not None:
            return True

        message.deleted_at = deleted_at

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
        session: Session | None = None,
    ) -> Message | None:
        statement = select(Message).where(
            Message.discord_message_id == discord_message_id
        )

        if session is not None:
            return session.scalar(statement)

        with SessionLocal() as session:
            return session.scalar(statement)

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
        start_at = ensure_utc(start_at)
        end_at = ensure_utc(end_at)

        with SessionLocal() as session:

            result = session.scalars(
                select(Message).where(
                    Message.guild_id == guild_id,
                    Message.channel_id.in_(channel_ids),
                    Message.created_at >= start_at,
                    Message.created_at < end_at,
                    Message.deleted_at.is_(None),
                )
            )

            return list(result)
