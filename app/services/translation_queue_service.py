import asyncio
from enum import Enum

from app.dto.translation_job_dto import TranslationJob


class EnqueueResult(Enum):
    ENQUEUED = "enqueued"
    ALREADY_PENDING = "already_pending"
    FULL = "full"


class TranslationQueueService:
    """Single-event-loop queue. Pending keys include waiting and active jobs."""

    def __init__(self, maxsize: int = 100):
        if maxsize <= 0:
            raise ValueError("maxsize must be positive")
        self._queue: asyncio.Queue[TranslationJob] = asyncio.Queue(maxsize=maxsize)
        self._pending: set[tuple[int, str, str]] = set()

    def enqueue(self, job: TranslationJob) -> EnqueueResult:
        if job.key in self._pending:
            return EnqueueResult.ALREADY_PENDING

        self._pending.add(job.key)
        try:
            self._queue.put_nowait(job)
        except asyncio.QueueFull:
            self._pending.remove(job.key)
            return EnqueueResult.FULL
        return EnqueueResult.ENQUEUED

    async def get(self) -> TranslationJob:
        return await self._queue.get()

    def complete(self, job: TranslationJob) -> None:
        self._pending.remove(job.key)
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()

    def discard_waiting(self) -> None:
        """Release waiting jobs on stop; producers must stop enqueueing first."""
        while True:
            try:
                job = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            self.complete(job)
