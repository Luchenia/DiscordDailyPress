from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.utils.content_hash import calculate_source_content_hash


@dataclass(frozen=True)
class TranslationSourceSnapshot:
    message_id: int
    content: str
    language: str
    deleted_at: datetime | None
    source_content_hash: str


class MessageTranslationRepository:
    def get_source_snapshot(self, message_id: int) -> TranslationSourceSnapshot | None:
        """Open/close the session in the caller's DB thread; return plain data."""
        with SessionLocal() as session:
            message = session.get(Message, message_id)
            if message is None:
                return None
            return TranslationSourceSnapshot(
                message_id=message.id,
                content=message.content,
                language=message.language,
                deleted_at=message.deleted_at,
                source_content_hash=calculate_source_content_hash(message.content),
            )

    def has_exact(self, message_id: int, target_language: str, source_hash: str) -> bool:
        # Consume the ORM result in the DB thread, not in the async worker.
        return self.get_by_source_content_hash(
            message_id, target_language, source_hash,
        ) is not None

    def save_if_current(
        self,
        source: TranslationSourceSnapshot,
        target_language: str,
        translated_content: str,
    ) -> bool:
        """Recheck source and insert atomically on SQLite; False means stale/missing.

        BEGIN IMMEDIATE prevents an edit/delete between the final check and insert.
        No provider work runs inside this short transaction.
        """
        with SessionLocal() as session:
            try:
                session.execute(text("BEGIN IMMEDIATE"))
                message = session.get(Message, source.message_id)
                if (
                    message is None
                    or message.deleted_at is not None
                    or calculate_source_content_hash(message.content)
                    != source.source_content_hash
                ):
                    session.rollback()
                    return False

                session.add(MessageTranslation(
                    message_id=source.message_id,
                    source_language=source.language,
                    target_language=target_language,
                    source_content_hash=source.source_content_hash,
                    translated_content=translated_content,
                ))
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                if self.has_exact(
                    source.message_id, target_language, source.source_content_hash,
                ):
                    return True
                raise

    def save(
        self,
        translation: MessageTranslation,
    ) -> MessageTranslation:
        with SessionLocal() as session:
            try:
                session.add(translation)
                session.commit()
                session.refresh(translation)

                return translation

            except IntegrityError:
                session.rollback()
                raise

    def get_by_source_content_hash(
        self,
        message_id: int,
        target_language: str,
        source_content_hash: str,
    ) -> MessageTranslation | None:
        with SessionLocal() as session:
            return session.scalar(
                select(MessageTranslation).where(
                    MessageTranslation.message_id == message_id,
                    MessageTranslation.target_language == target_language,
                    MessageTranslation.source_content_hash
                    == source_content_hash,
                )
            )

    def get_current(
        self,
        message_id: int,
        target_language: str,
    ) -> MessageTranslation | None:
        with SessionLocal() as session:
            message = session.get(Message, message_id)

            if message is None:
                return None

            current_content_hash = calculate_source_content_hash(
                message.content
            )

            return session.scalar(
                select(MessageTranslation).where(
                    MessageTranslation.message_id == message_id,
                    MessageTranslation.target_language == target_language,
                    MessageTranslation.source_content_hash
                    == current_content_hash,
                )
            )
