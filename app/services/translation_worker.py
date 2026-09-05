import asyncio
from typing import Callable, TypeVar

from app.core.logger import get_logger
from app.dto.translation_job_dto import TranslationJob
from app.repositories.message_translation_repository import MessageTranslationRepository
from app.services.translation_provider import TranslationProvider
from app.services.translation_queue_service import TranslationQueueService


logger = get_logger(__name__)
T = TypeVar("T")


class TranslationWorker:
    """One consumer, no retries or automatic stale-job enqueueing."""

    def __init__(
        self,
        queue: TranslationQueueService,
        provider: TranslationProvider,
        repository: MessageTranslationRepository | None = None,
    ):
        self.queue = queue
        self.provider = provider
        self.repository = repository if repository is not None else MessageTranslationRepository()
        self._task: asyncio.Task | None = None
        self._stop_lock = asyncio.Lock()

    def start(self) -> None:
        if self._stop_lock.locked():
            raise RuntimeError("Translation worker is stopping")
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="translation-worker")

    async def stop(self) -> None:
        """Cancel active work and discard waiting jobs after producers stop.

        Call queue.join() before stop() if accepted work should finish first.
        An already running DB thread finishes before stop returns.
        """
        async with self._stop_lock:
            task = self._task
            try:
                if task is not None:
                    if not task.done():
                        task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        logger.exception("Translation worker stopped unexpectedly")
            finally:
                self._task = None
                self.queue.discard_waiting()

    @staticmethod
    async def _db_call(function: Callable[..., T], *args) -> T:
        task = asyncio.create_task(asyncio.to_thread(function, *args))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            # to_thread cancellation cannot stop its underlying thread.
            try:
                await task
            except Exception:
                logger.exception("Translation DB operation failed during shutdown")
            raise

    async def _run(self) -> None:
        while True:
            job = await self.queue.get()
            try:
                await self._process(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Translation job failed: %s", job.key)
            finally:
                self.queue.complete(job)

    async def _process(self, job: TranslationJob) -> None:
        source = await self._db_call(self.repository.get_source_snapshot, job.message_id)
        if (
            source is None
            or source.deleted_at is not None
            or source.source_content_hash != job.source_content_hash
        ):
            return
        if await self._db_call(
            self.repository.has_exact,
            job.message_id, job.target_language, job.source_content_hash,
        ):
            return

        translated_content = await self.provider.translate(
            text=source.content,
            source_language=source.language,
            target_language=job.target_language,
        )
        await self._db_call(
            self.repository.save_if_current, source, job.target_language, translated_content,
        )
