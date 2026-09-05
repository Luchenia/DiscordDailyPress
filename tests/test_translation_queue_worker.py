import asyncio
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
import threading

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.dto.translation_job_dto import TranslationJob
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.repositories import message_translation_repository
from app.repositories.message_translation_repository import MessageTranslationRepository
from app.services.translation_queue_service import EnqueueResult, TranslationQueueService
from app.services.translation_worker import TranslationWorker
from app.utils.content_hash import calculate_source_content_hash


@pytest.fixture
def database(tmp_path, monkeypatch):
    # Real, separate SQLite connections for worker threads; never the app DB.
    engine = create_engine(f"sqlite:///{(tmp_path / 'translations.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(message_translation_repository, "SessionLocal", sessions)
    with sessions.begin() as session:
        for message_id in (1, 2):
            session.add(Message(
                id=message_id,
                discord_message_id=1000 + message_id,
                guild_id=100,
                guild_name="test",
                channel_id=200,
                channel_name="general",
                author_id=300,
                author_username="user",
                author_display_name="User",
                content="hello",
                language="en",
                created_at=datetime.now(UTC),
            ))
    yield sessions
    engine.dispose()


def make_job(message_id=1, content="hello", target="ko"):
    return TranslationJob(message_id, target, calculate_source_content_hash(content))


def change_message(sessions, **values):
    with sessions.begin() as session:
        message = session.get(Message, 1)
        for name, value in values.items():
            setattr(message, name, value)


def insert_translation(sessions, translated_content="cached"):
    with sessions.begin() as session:
        session.add(MessageTranslation(
            message_id=1,
            source_language="en",
            target_language="ko",
            source_content_hash=make_job().source_content_hash,
            translated_content=translated_content,
        ))


def translation_values(sessions):
    with sessions() as session:
        return [
            (row.message_id, row.source_language, row.target_language, row.translated_content)
            for row in session.scalars(select(MessageTranslation).order_by(MessageTranslation.id))
        ]


class FakeProvider:
    def __init__(self, hook=None):
        self.calls = []
        self.hook = hook

    async def translate(self, text, source_language, target_language):
        self.calls.append((text, source_language, target_language))
        if self.hook is not None:
            return await self.hook()
        return "translated"


async def finish(queue, worker):
    worker.start()
    task = worker._task
    try:
        await asyncio.wait_for(queue.join(), timeout=5)
        assert not task.done()
        assert not queue._pending
    finally:
        await worker.stop()
    assert task.done()
    assert worker._task is None


def test_job_is_immutable_and_queue_is_bounded():
    job = make_job()
    with pytest.raises(FrozenInstanceError):
        job.message_id = 2
    assert job.key == (1, "ko", calculate_source_content_hash("hello"))
    queue = TranslationQueueService()
    for message_id in range(100):
        assert queue.enqueue(make_job(message_id)) is EnqueueResult.ENQUEUED
    assert queue.enqueue(make_job(101)) is EnqueueResult.FULL
    assert queue.enqueue(make_job(0)) is EnqueueResult.ALREADY_PENDING
    for maxsize in (0, -1):
        with pytest.raises(ValueError):
            TranslationQueueService(maxsize)


def test_queue_full_does_not_leak_pending_key():
    async def run():
        queue = TranslationQueueService(maxsize=1)
        assert queue.enqueue(make_job(1)) is EnqueueResult.ENQUEUED
        assert queue.enqueue(make_job(2)) is EnqueueResult.FULL
        queue.complete(await queue.get())
        assert queue.enqueue(make_job(2)) is EnqueueResult.ENQUEUED
        queue.complete(await queue.get())
        await asyncio.wait_for(queue.join(), 1)
        assert not queue._pending
    asyncio.run(run())


def test_normal_job_preserves_raw_data_and_uses_only_db_threads(database):
    async def run():
        loop_thread = threading.get_ident()
        db_threads = []
        engine = database.kw["bind"]

        def record_thread(*args):
            db_threads.append(threading.get_ident())

        event.listen(engine, "before_cursor_execute", record_thread)
        queue = TranslationQueueService()
        provider = FakeProvider()
        worker = TranslationWorker(queue, provider)
        try:
            assert queue.enqueue(make_job()) is EnqueueResult.ENQUEUED
            assert queue.enqueue(make_job()) is EnqueueResult.ALREADY_PENDING
            await finish(queue, worker)
        finally:
            event.remove(engine, "before_cursor_execute", record_thread)
        assert db_threads and loop_thread not in db_threads
        assert provider.calls == [("hello", "en", "ko")]
        assert translation_values(database) == [(1, "en", "ko", "translated")]
        with database() as session:
            message = session.get(Message, 1)
            assert (message.content, message.language) == ("hello", "en")
        # Completion released the key; a subsequent request becomes a cache hit.
        assert queue.enqueue(make_job()) is EnqueueResult.ENQUEUED
        await finish(queue, worker)
        assert len(provider.calls) == 1
    asyncio.run(run())


def test_duplicate_active_job_calls_provider_once(database):
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()

        async def blocked():
            entered.set()
            await release.wait()
            return "translated"

        queue = TranslationQueueService()
        provider = FakeProvider(blocked)
        worker = TranslationWorker(queue, provider)
        queue.enqueue(make_job())
        worker.start()
        first_task = worker._task
        worker.start()
        assert worker._task is first_task
        try:
            await asyncio.wait_for(entered.wait(), 5)
            assert queue.enqueue(make_job()) is EnqueueResult.ALREADY_PENDING
            release.set()
            await asyncio.wait_for(queue.join(), 5)
            assert len(provider.calls) == 1
        finally:
            await worker.stop()
    asyncio.run(run())


def test_existing_exact_translation_skips_provider(database):
    insert_translation(database)

    async def run():
        queue = TranslationQueueService()
        provider = FakeProvider()
        queue.enqueue(make_job())
        await finish(queue, TranslationWorker(queue, provider))
        assert provider.calls == []
        assert translation_values(database) == [(1, "en", "ko", "cached")]
    asyncio.run(run())


@pytest.mark.parametrize("state", ["edited", "deleted", "missing"])
def test_ineligible_source_skips_provider_without_requeue(database, state):
    async def run():
        queue = TranslationQueueService()
        provider = FakeProvider()
        queue.enqueue(make_job(999 if state == "missing" else 1))
        if state == "edited":
            change_message(database, content="hello world")
        elif state == "deleted":
            insert_translation(database)
            change_message(database, deleted_at=datetime.now(UTC))
        await finish(queue, TranslationWorker(queue, provider))
        assert not provider.calls
        assert queue._queue.empty()
        assert translation_values(database) == (
            [(1, "en", "ko", "cached")] if state == "deleted" else []
        )
    asyncio.run(run())


@pytest.mark.parametrize("state", ["edited", "deleted"])
def test_source_changes_during_provider_discard_result(database, state):
    async def run():
        async def mutate():
            values = {"content": "hello world"} if state == "edited" else {
                "deleted_at": datetime.now(UTC),
            }
            await asyncio.to_thread(change_message, database, **values)
            return "obsolete translation"

        queue = TranslationQueueService()
        provider = FakeProvider(mutate)
        queue.enqueue(make_job())
        await finish(queue, TranslationWorker(queue, provider))
        assert len(provider.calls) == 1
        assert translation_values(database) == []
        assert queue._queue.empty()
    asyncio.run(run())


def test_source_language_uses_pre_provider_snapshot(database):
    async def run():
        async def mutate_language():
            await asyncio.to_thread(change_message, database, language="unknown")
            return "translated"

        queue = TranslationQueueService()
        provider = FakeProvider(mutate_language)
        queue.enqueue(make_job())
        await finish(queue, TranslationWorker(queue, provider))
        assert translation_values(database) == [(1, "en", "ko", "translated")]
        with database() as session:
            message = session.get(Message, 1)
            assert (message.content, message.language) == ("hello", "unknown")
    asyncio.run(run())


def test_duplicate_db_save_race_converges_after_rollback(database, caplog):
    async def run():
        async def concurrent_save():
            await asyncio.to_thread(insert_translation, database, "race winner")
            return "race loser"

        queue = TranslationQueueService()
        provider = FakeProvider(concurrent_save)
        queue.enqueue(make_job())
        await finish(queue, TranslationWorker(queue, provider))
        assert len(provider.calls) == 1
        assert translation_values(database) == [(1, "en", "ko", "race winner")]
        assert "Translation job failed" not in caplog.text
    asyncio.run(run())


@pytest.mark.parametrize("failure", ["provider", "integrity"])
def test_failed_job_cleans_up_and_worker_continues(database, caplog, failure):
    async def run():
        async def fail_once():
            if len(provider.calls) == 1:
                if failure == "provider":
                    raise RuntimeError("fake provider failure")
                return None  # NOT NULL violation with no existing exact row.
            return "translated"

        provider = FakeProvider(fail_once)
        queue = TranslationQueueService()
        queue.enqueue(make_job(1))
        queue.enqueue(make_job(2))
        await finish(queue, TranslationWorker(queue, provider))
        assert len(provider.calls) == 2
        assert translation_values(database) == [(2, "en", "ko", "translated")]
        assert "Translation job failed" in caplog.text
        assert queue.enqueue(make_job(1)) is EnqueueResult.ENQUEUED
        queue.discard_waiting()
        await asyncio.wait_for(queue.join(), 1)
    asyncio.run(run())


def test_stop_cancels_active_provider_discards_waiting_and_releases_keys(database):
    async def run():
        entered, cancelled = asyncio.Event(), asyncio.Event()

        async def blocked():
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        queue = TranslationQueueService()
        provider = FakeProvider(blocked)
        worker = TranslationWorker(queue, provider)
        queue.enqueue(make_job(1))
        queue.enqueue(make_job(2))
        worker.start()
        task = worker._task
        try:
            await asyncio.wait_for(entered.wait(), 5)
        finally:
            await worker.stop()
        await worker.stop()
        await asyncio.wait_for(queue.join(), 1)
        assert cancelled.is_set()
        assert task.cancelled()
        assert not queue._pending and queue._queue.empty()
        assert translation_values(database) == []
        assert worker._task is None
    asyncio.run(run())


def test_stop_waits_for_db_thread_and_does_not_leave_tasks(database, monkeypatch):
    async def run():
        entered, release = threading.Event(), threading.Event()
        repository = MessageTranslationRepository()
        original = repository.get_source_snapshot

        def blocked_read(message_id):
            entered.set()
            assert release.wait(5)
            return original(message_id)

        monkeypatch.setattr(repository, "get_source_snapshot", blocked_read)
        queue = TranslationQueueService()
        provider = FakeProvider()
        worker = TranslationWorker(queue, provider, repository)
        queue.enqueue(make_job())
        worker.start()
        task = worker._task
        stop_task = None
        try:
            assert await asyncio.to_thread(entered.wait, 5)
            stop_task = asyncio.create_task(worker.stop())
            await asyncio.sleep(0)
            assert not stop_task.done()
        finally:
            release.set()
            if stop_task is not None:
                await asyncio.wait_for(stop_task, 5)
            else:
                await worker.stop()
        await asyncio.wait_for(queue.join(), 1)
        assert task.done()
        assert not provider.calls
        assert not queue._pending
        assert not [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    asyncio.run(run())
