import asyncio
from datetime import UTC, datetime
from unittest.mock import Mock

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.dto.discord_message_dto import DiscordMessageDTO
from app.models.collection_channel import CollectionChannel
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.repositories import (
    collection_channel_repository,
    message_repository,
    message_translation_repository,
)
from app.services import message_service
from app.services.message_service import MessageService
from app.services.translation_producer_service import TranslationProducerService
from app.services.translation_queue_service import TranslationQueueService
from app.services.translation_worker import TranslationWorker
from app.utils.content_hash import calculate_source_content_hash


class FakeTranslationProvider:
    def __init__(self):
        self.calls = []

    async def translate(self, text, source_language, target_language):
        self.calls.append((text, source_language, target_language))
        return {
            "Hello, Chronicle!": "크로니클 안녕!",
            "またね!": "나중에 봐!",
        }[text]


def test_conversation_flush_translates_enabled_channel_without_changing_raw_data(
    tmp_path,
    monkeypatch,
):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'translation-pipeline.db').as_posix()}"
    )
    sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(message_repository, "SessionLocal", sessions)
    monkeypatch.setattr(message_service, "SessionLocal", sessions)
    monkeypatch.setattr(collection_channel_repository, "SessionLocal", sessions)
    monkeypatch.setattr(message_translation_repository, "SessionLocal", sessions)

    with sessions.begin() as session:
        session.add(CollectionChannel(
            guild_id=100,
            channel_id=200,
            channel_name="general",
            enabled=True,
        ))

    queue = TranslationQueueService()
    provider = FakeTranslationProvider()
    producer = TranslationProducerService(queue, target_language="ko")
    producer.start()
    service = MessageService(translation_producer=producer)
    service.language_service.detect = Mock(side_effect=["en", "ja"])
    service.conversation_buffer.language_service.detect = Mock(return_value="ko")

    source_texts = ["Hello, Chronicle!", "またね!"]
    saved = []
    created_at = datetime.now(UTC)
    for offset, source_text in enumerate(source_texts, start=1):
        saved.append(service.save(DiscordMessageDTO(
            discord_message_id=1000 + offset,
            guild_id=100,
            guild_name="Test Guild",
            channel_id=200,
            channel_name="general",
            author_id=300,
            author_username="test-user",
            author_display_name="Test User",
            is_bot=False,
            content=source_text,
            has_attachment=False,
            attachment_count=0,
            created_at=created_at,
        )))

    async def run_pipeline():
        worker = TranslationWorker(queue, provider)
        worker.start()
        try:
            flushed = service.conversation_buffer.flush_all()
            assert len(flushed) == 1
            await asyncio.wait_for(queue.join(), timeout=5)
        finally:
            producer.stop()
            await worker.stop()

    try:
        asyncio.run(run_pipeline())

        with sessions() as session:
            raw_messages = list(session.scalars(select(Message).order_by(Message.id)))
            translations = list(session.scalars(
                select(MessageTranslation).order_by(MessageTranslation.message_id)
            ))

        assert all(result is not None for result in saved)
        assert [message.id for message in raw_messages] == [
            result.message.id for result in saved
        ]
        assert [message.content for message in raw_messages] == source_texts
        assert [message.language for message in raw_messages] == ["en", "ja"]
        assert [translation.message_id for translation in translations] == [
            message.id for message in raw_messages
        ]
        assert [translation.source_language for translation in translations] == [
            "en",
            "ja",
        ]
        assert all(translation.target_language == "ko" for translation in translations)
        assert [translation.source_content_hash for translation in translations] == [
            calculate_source_content_hash(source_text)
            for source_text in source_texts
        ]
        assert [translation.translated_content for translation in translations] == [
            "크로니클 안녕!",
            "나중에 봐!",
        ]
        assert provider.calls == [
            ("Hello, Chronicle!", "en", "ko"),
            ("またね!", "ja", "ko"),
        ]
    finally:
        engine.dispose()
