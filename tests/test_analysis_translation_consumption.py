from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.repositories import message_repository, message_translation_repository
from app.repositories.message_translation_repository import (
    MessageTranslationRepository,
)
from app.services.analysis_service import AnalysisService
from app.services.analysis_text_resolver import AnalysisTextResolver
from app.utils.content_hash import calculate_source_content_hash


@pytest.fixture
def test_session_local(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(message_repository, "SessionLocal", sessions)
    monkeypatch.setattr(message_translation_repository, "SessionLocal", sessions)
    yield sessions
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def make_message(
    discord_message_id: int,
    content: str,
    language: str | None,
    created_at: datetime,
    *,
    deleted_at: datetime | None = None,
) -> Message:
    return Message(
        discord_message_id=discord_message_id,
        guild_id=100,
        guild_name="Test Guild",
        channel_id=200,
        channel_name="general",
        author_id=300,
        author_username="test-user",
        author_display_name="Test User",
        is_bot=False,
        content=content,
        language=language,
        has_attachment=False,
        attachment_count=0,
        created_at=created_at,
        deleted_at=deleted_at,
    )


def make_translation(
    message: Message,
    source_content: str,
    translated_content: str,
) -> MessageTranslation:
    return MessageTranslation(
        message_id=message.id,
        source_language=message.language,
        target_language="ko",
        source_content_hash=calculate_source_content_hash(source_content),
        translated_content=translated_content,
    )


def test_analysis_dataset_resolves_current_translations_in_one_batch(
    test_session_local,
):
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    current = make_message(1001, "hello", "en", base_time)
    stale = make_message(1002, "edited source", "en", base_time + timedelta(minutes=1))
    missing = make_message(1003, "no translation", "en", base_time + timedelta(minutes=2))
    same_language = make_message(1004, "이미 한국어", "ko", base_time + timedelta(minutes=3))
    edited = make_message(1005, "new version", "en", base_time + timedelta(minutes=4))
    deleted = make_message(
        1006,
        "deleted source",
        "en",
        base_time + timedelta(minutes=5),
        deleted_at=base_time + timedelta(hours=1),
    )

    with test_session_local.begin() as session:
        session.add_all([current, stale, missing, same_language, edited, deleted])
        session.flush()
        current_translation = make_translation(current, "hello", "안녕하세요")
        stale_translation = make_translation(stale, "old source", "오래된 번역")
        redundant_translation = make_translation(
            same_language,
            "이미 한국어",
            "중복 번역",
        )
        old_edited_translation = make_translation(
            edited,
            "old version",
            "이전 버전",
        )
        new_edited_translation = make_translation(
            edited,
            "new version",
            "새 버전",
        )
        deleted_translation = make_translation(
            deleted,
            "deleted source",
            "삭제된 번역",
        )
        session.add_all([
            current_translation,
            stale_translation,
            redundant_translation,
            old_edited_translation,
            new_edited_translation,
            deleted_translation,
        ])
        session.flush()
        message_ids = {
            "current": current.id,
            "stale": stale.id,
            "missing": missing.id,
            "edited": edited.id,
        }
        current_translation_id = current_translation.id
        new_edited_translation_id = new_edited_translation.id

    translation_repository = MessageTranslationRepository()
    batch_reader = Mock(wraps=translation_repository, spec=MessageTranslationRepository)
    service = AnalysisService(
        text_resolver=AnalysisTextResolver(repository=batch_reader),
    )
    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[200],
        start_at=base_time,
        end_at=base_time + timedelta(days=1),
    )

    dataset = service.build_dataset(scope, output_language="ko")
    by_discord_id = {message.message_id: message for message in dataset.messages}

    assert set(by_discord_id) == {1001, 1002, 1003, 1004, 1005}
    assert by_discord_id[1001].content == "hello"
    assert by_discord_id[1001].analysis_content == "안녕하세요"
    assert by_discord_id[1001].analysis_language == "ko"
    assert by_discord_id[1001].analysis_content_source is AnalysisTextSource.TRANSLATION
    assert by_discord_id[1001].translation_id == current_translation_id

    assert by_discord_id[1002].analysis_content == "edited source"
    assert by_discord_id[1002].analysis_language == "en"
    assert by_discord_id[1002].analysis_content_source is AnalysisTextSource.RAW
    assert by_discord_id[1002].translation_id is None

    assert by_discord_id[1003].analysis_content == "no translation"
    assert by_discord_id[1003].analysis_content_source is AnalysisTextSource.RAW
    assert by_discord_id[1004].analysis_content == "이미 한국어"
    assert by_discord_id[1004].analysis_content_source is AnalysisTextSource.RAW

    assert by_discord_id[1005].analysis_content == "새 버전"
    assert by_discord_id[1005].translation_id == new_edited_translation_id
    assert by_discord_id[1005].source_content_hash == (
        calculate_source_content_hash("new version")
    )

    batch_reader.get_current_batch.assert_called_once()
    hashes, target_language = batch_reader.get_current_batch.call_args.args
    assert target_language == "ko"
    assert hashes == {
        message_ids["current"]: calculate_source_content_hash("hello"),
        message_ids["stale"]: calculate_source_content_hash("edited source"),
        message_ids["missing"]: calculate_source_content_hash("no translation"),
        message_ids["edited"]: calculate_source_content_hash("new version"),
    }

    with test_session_local() as session:
        stored_content = {
            message.discord_message_id: message.content
            for message in session.scalars(select(Message))
        }
        translation_count = session.scalar(
            select(func.count()).select_from(MessageTranslation)
        )

    assert stored_content == {
        1001: "hello",
        1002: "edited source",
        1003: "no translation",
        1004: "이미 한국어",
        1005: "new version",
        1006: "deleted source",
    }
    assert translation_count == 6


def test_same_language_resolution_does_not_read_translations():
    repository = Mock(spec=MessageTranslationRepository)
    message = make_message(
        1001,
        "이미 한국어",
        "KO",
        datetime(2026, 9, 8, tzinfo=UTC),
    )
    resolver = AnalysisTextResolver(repository=repository)

    resolved = resolver.resolve_many([message], "ko")

    assert resolved[0].content == "이미 한국어"
    assert resolved[0].content_source is AnalysisTextSource.RAW
    repository.get_current_batch.assert_not_called()


@pytest.mark.parametrize("stored_language", [None, "", "   "])
def test_nullable_or_blank_language_uses_unknown_raw_fallback(stored_language):
    translation_repository = Mock(spec=MessageTranslationRepository)
    translation_repository.get_current_batch.return_value = {}
    message = make_message(
        1001,
        "source text",
        stored_language,
        datetime(2026, 9, 8, tzinfo=UTC),
    )
    message.id = 1
    raw_language = message.language
    source_repository = Mock()
    source_repository.get_by_analysis_scope.return_value = [message]
    service = AnalysisService(
        repository=source_repository,
        text_resolver=AnalysisTextResolver(repository=translation_repository),
    )
    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[200],
        start_at=datetime(2026, 9, 8, tzinfo=UTC),
        end_at=datetime(2026, 9, 9, tzinfo=UTC),
    )

    dataset = service.build_dataset(scope, output_language="ko")
    prepared = dataset.messages[0]

    assert message.language == raw_language
    assert prepared.language == "unknown"
    assert prepared.analysis_language == "unknown"
    assert prepared.analysis_content == "source text"
    assert prepared.analysis_content_source is AnalysisTextSource.RAW
    assert dataset.metadata.language_distribution == {"unknown": 1.0}
    translation_repository.get_current_batch.assert_called_once_with(
        {1: calculate_source_content_hash("source text")},
        "ko",
    )


def test_deleted_message_is_rejected_by_text_resolver():
    repository = Mock(spec=MessageTranslationRepository)
    message = make_message(
        1001,
        "deleted",
        "en",
        datetime(2026, 9, 8, tzinfo=UTC),
        deleted_at=datetime(2026, 9, 8, 1, tzinfo=UTC),
    )
    resolver = AnalysisTextResolver(repository=repository)

    with pytest.raises(ValueError, match="deleted messages"):
        resolver.resolve_many([message], "ko")

    repository.get_current_batch.assert_not_called()
