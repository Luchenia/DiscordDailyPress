from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database.session import SessionLocal
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.utils.content_hash import calculate_source_content_hash


class MessageTranslationRepository:
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
