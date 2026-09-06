from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Config
from app.database.base import Base
from app.dto.conversation_result_dto import ConversationResultDTO
from app.dto.discord_message_dto import DiscordMessageDTO
from app.dto.translation_job_dto import TranslationSourceCandidate
from app.models.message import Message
from app.repositories import message_history_repository, message_repository
from app.services import message_service
from app.services.message_service import MessageService
from app.services.translation_producer_service import (
    TranslationProducerService,
    TranslationProductionResult,
)
from app.services.translation_queue_service import TranslationQueueService
from app.utils.content_hash import calculate_source_content_hash


def make_candidate(
    message_id=1,
    *,
    guild_id=100,
    channel_id=200,
    language="en",
    content="hello",
    deleted_at=None,
):
    return TranslationSourceCandidate(
        message_id=message_id,
        guild_id=guild_id,
        channel_id=channel_id,
        source_language=language,
        source_content_hash=calculate_source_content_hash(content),
        deleted_at=deleted_at,
    )


def start_producer(queue=None, *, enabled_channels=(200,), target="ko"):
    queue = queue or TranslationQueueService()
    repository = Mock()
    repository.get_enabled_channel_ids.return_value = list(enabled_channels)
    producer = TranslationProducerService(
        queue,
        target,
        collection_channel_repository=repository,
    )
    producer.start()
    return producer, queue, repository


def pop_job(queue):
    job = queue._queue.get_nowait()
    queue.complete(job)
    return job


def test_enabled_collection_channel_enqueues_configured_target():
    producer, queue, repository = start_producer(target="ja")
    candidate = make_candidate()

    results = producer.enqueue_candidates([candidate])

    assert results == {1: TranslationProductionResult.ENQUEUED}
    job = pop_job(queue)
    assert job.message_id == 1
    assert job.target_language == "ja"
    assert job.source_content_hash == candidate.source_content_hash
    repository.get_enabled_channel_ids.assert_called_once_with(100)


@pytest.mark.parametrize("enabled_channels", [(), (201,)])
def test_disabled_or_non_target_channel_is_not_enqueued(enabled_channels):
    producer, queue, _ = start_producer(enabled_channels=enabled_channels)

    results = producer.enqueue_candidates([make_candidate()])

    assert results == {1: TranslationProductionResult.INACTIVE_CHANNEL}
    assert queue._queue.empty()


def test_same_source_and_target_language_skips_without_scope_query():
    producer, queue, repository = start_producer(target=" KO ")

    results = producer.enqueue_candidates([
        make_candidate(language="ko"),
    ])

    assert results == {1: TranslationProductionResult.SAME_LANGUAGE}
    assert queue._queue.empty()
    repository.get_enabled_channel_ids.assert_not_called()


def test_unknown_source_language_is_enqueued_for_gemini_auto_detect():
    producer, queue, _ = start_producer()
    candidate = make_candidate(language="unknown")

    results = producer.enqueue_candidates([candidate])

    assert results == {1: TranslationProductionResult.ENQUEUED}
    assert pop_job(queue).source_content_hash == candidate.source_content_hash


def test_queue_full_does_not_raise_or_leak_second_pending_key(caplog):
    producer, queue, _ = start_producer(TranslationQueueService(maxsize=1))

    results = producer.enqueue_candidates([
        make_candidate(1, content="first"),
        make_candidate(2, content="second"),
    ])

    assert results == {
        1: TranslationProductionResult.ENQUEUED,
        2: TranslationProductionResult.FULL,
    }
    assert queue._pending == {
        (1, "ko", calculate_source_content_hash("first")),
    }
    assert "Translation queue full; skipped message #2" in caplog.text
    pop_job(queue)


def test_edit_creates_a_new_hash_job_while_stale_job_remains_safe():
    producer, queue, _ = start_producer()
    original = make_candidate(content="before")
    edited = make_candidate(content="after")

    assert producer.enqueue_candidates([original]) == {
        1: TranslationProductionResult.ENQUEUED,
    }
    assert producer.enqueue_candidates([edited]) == {
        1: TranslationProductionResult.ENQUEUED,
    }

    jobs = [pop_job(queue), pop_job(queue)]
    assert [job.source_content_hash for job in jobs] == [
        calculate_source_content_hash("before"),
        calculate_source_content_hash("after"),
    ]


def test_deleted_message_is_not_enqueued():
    producer, queue, repository = start_producer()

    results = producer.enqueue_candidates([
        make_candidate(deleted_at=datetime.now(UTC)),
    ])

    assert results == {1: TranslationProductionResult.DELETED}
    assert queue._queue.empty()
    repository.get_enabled_channel_ids.assert_not_called()


def test_stopped_producer_rejects_new_jobs_without_scope_query():
    producer, queue, repository = start_producer()
    producer.stop()

    results = producer.enqueue_candidates([make_candidate()])

    assert results == {1: TranslationProductionResult.NOT_ACCEPTING}
    assert queue._queue.empty()
    repository.get_enabled_channel_ids.assert_not_called()


def test_default_target_language_is_korean():
    assert Config().translation_target_language == "ko"


@pytest.fixture
def database(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sessions = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(message_repository, "SessionLocal", sessions)
    monkeypatch.setattr(message_history_repository, "SessionLocal", sessions)
    monkeypatch.setattr(message_service, "SessionLocal", sessions)
    yield sessions
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def make_dto(content="hello", *, edited_at=None):
    return DiscordMessageDTO(
        discord_message_id=1001,
        guild_id=100,
        guild_name="Test Guild",
        channel_id=200,
        channel_name="general",
        author_id=300,
        author_username="test-user",
        author_display_name="Test User",
        is_bot=False,
        content=content,
        has_attachment=False,
        attachment_count=0,
        reply_to_message_id=None,
        created_at=datetime.now(UTC),
        edited_at=edited_at,
    )


def test_conversation_producer_failure_keeps_raw_and_language_update(
    database,
    caplog,
):
    producer = Mock()
    producer.enqueue_candidates.side_effect = RuntimeError("producer failed")
    service = MessageService(translation_producer=producer)
    service.save(make_dto("hello"))
    service.language_service.detect = Mock(return_value="en")

    result = ConversationResultDTO(
        message_ids=[1001],
        author_id=300,
        channel_id=200,
        text="hello",
        language="en",
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
    )
    service.process_conversation_result(result)

    with database() as session:
        stored = session.scalar(select(Message))
        assert stored.content == "hello"
        assert stored.language == "en"
    producer.enqueue_candidates.assert_called_once()
    assert "Translation producer failed for 1 message(s)" in caplog.text


def test_edit_enqueues_only_after_commit_with_new_content_hash(database):
    producer = Mock()

    def assert_committed(candidates):
        with database() as session:
            stored = session.scalar(select(Message))
            assert stored.content == "after"
            assert stored.language == "en"

    producer.enqueue_candidates.side_effect = assert_committed
    service = MessageService(translation_producer=producer)
    service.save(make_dto("before"))
    service.language_service.detect = Mock(return_value="en")

    updated = service.update(
        make_dto("after", edited_at=datetime.now(UTC))
    )

    assert updated.content == "after"
    candidate = producer.enqueue_candidates.call_args.args[0][0]
    assert candidate.source_language == "en"
    assert candidate.source_content_hash == calculate_source_content_hash("after")
