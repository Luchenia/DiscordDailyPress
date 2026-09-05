import asyncio
from unittest.mock import AsyncMock, Mock

from discord.ext import commands

from app.bot.bot import ChronicleBot
from app.dto.translation_job_dto import TranslationJob
from app.services.translation_queue_service import EnqueueResult


class FakeProvider:
    async def translate(self, text, source_language, target_language):
        return "translated"


def stub_discord_setup(bot: ChronicleBot) -> None:
    bot.tree.set_translator = AsyncMock()
    bot.analysis_command.register = Mock()
    bot.reporter_command.register = Mock()
    bot.tree.copy_global_to = Mock()
    bot.tree.clear_commands = Mock()
    bot.tree.sync = AsyncMock()


def stub_shutdown(monkeypatch, bot: ChronicleBot):
    conversation_stop = AsyncMock()
    super_close = AsyncMock()
    bot.message_collector.stop_cleanup = conversation_stop
    monkeypatch.setattr(commands.Bot, "close", super_close)
    return conversation_stop, super_close


def make_job() -> TranslationJob:
    return TranslationJob(
        message_id=1,
        target_language="ko",
        source_content_hash="source-hash",
    )


def test_provider_none_keeps_translation_lifecycle_disabled(monkeypatch):
    async def scenario():
        bot = ChronicleBot()
        stub_discord_setup(bot)
        conversation_stop, super_close = stub_shutdown(monkeypatch, bot)

        assert bot.translation_queue is None
        assert bot.translation_worker is None
        assert bot.accepts_translation_jobs is False

        await bot.setup_hook()

        assert bot.accepts_translation_jobs is False

        await bot.close()

        conversation_stop.assert_awaited_once()
        super_close.assert_awaited_once()

    asyncio.run(scenario())


def test_provider_starts_one_worker_across_repeated_setup(monkeypatch):
    async def scenario():
        bot = ChronicleBot(translation_provider=FakeProvider())
        stub_discord_setup(bot)
        stub_shutdown(monkeypatch, bot)

        assert bot.translation_queue is not None
        assert bot.translation_worker is not None
        assert bot.translation_queue._queue.maxsize == 100

        await bot.setup_hook()
        first_task = bot.translation_worker._task

        await bot.setup_hook()

        assert first_task is not None
        assert bot.translation_worker._task is first_task
        assert bot.accepts_translation_jobs is True

        await bot.close()

        assert bot.translation_worker._task is None
        assert bot.accepts_translation_jobs is False

    asyncio.run(scenario())


def test_shutdown_drains_accepted_job_and_stops_worker(monkeypatch):
    async def scenario():
        bot = ChronicleBot(translation_provider=FakeProvider())
        stub_discord_setup(bot)
        stub_shutdown(monkeypatch, bot)
        processed = AsyncMock()
        bot.translation_worker._process = processed

        await bot.setup_hook()

        job = make_job()
        assert bot.translation_queue.enqueue(job) is EnqueueResult.ENQUEUED

        await bot.close()

        processed.assert_awaited_once_with(job)
        assert bot.translation_worker._task is None
        assert bot.translation_queue._pending == set()
        assert bot.accepts_translation_jobs is False

    asyncio.run(scenario())


def test_shutdown_timeout_stops_worker_without_waiting_five_seconds(monkeypatch):
    async def scenario():
        bot = ChronicleBot(translation_provider=FakeProvider())
        stub_discord_setup(bot)
        stub_shutdown(monkeypatch, bot)
        entered = asyncio.Event()
        never_finish = asyncio.Event()

        async def block_processing(job):
            entered.set()
            await never_finish.wait()

        bot.translation_worker._process = block_processing
        bot.TRANSLATION_DRAIN_TIMEOUT_SECONDS = 0.01

        await bot.setup_hook()
        assert bot.translation_queue.enqueue(make_job()) is EnqueueResult.ENQUEUED
        await asyncio.wait_for(entered.wait(), timeout=1)

        await asyncio.wait_for(bot.close(), timeout=1)

        assert bot.translation_worker._task is None
        assert bot.translation_queue._pending == set()
        assert bot.accepts_translation_jobs is False

    asyncio.run(scenario())


def test_translation_shutdown_failure_does_not_skip_other_shutdown(monkeypatch):
    async def scenario():
        bot = ChronicleBot(translation_provider=FakeProvider())
        conversation_stop, super_close = stub_shutdown(monkeypatch, bot)
        bot._shutdown_translation = AsyncMock(
            side_effect=RuntimeError("translation shutdown failed"),
        )

        await bot.close()

        bot._shutdown_translation.assert_awaited_once()
        conversation_stop.assert_awaited_once()
        super_close.assert_awaited_once()

    asyncio.run(scenario())


def test_conversation_shutdown_failure_does_not_skip_translation_or_super(monkeypatch):
    async def scenario():
        bot = ChronicleBot(translation_provider=FakeProvider())
        translation_stop = AsyncMock()
        bot.translation_worker.stop = translation_stop
        bot.message_collector.stop_cleanup = AsyncMock(
            side_effect=RuntimeError("conversation shutdown failed"),
        )
        super_close = AsyncMock()
        monkeypatch.setattr(commands.Bot, "close", super_close)

        await bot.close()

        translation_stop.assert_awaited_once()
        bot.message_collector.stop_cleanup.assert_awaited_once()
        super_close.assert_awaited_once()

    asyncio.run(scenario())
