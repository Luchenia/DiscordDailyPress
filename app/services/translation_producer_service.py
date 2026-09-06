from enum import Enum
from typing import Iterable

from app.core.logger import get_logger
from app.dto.translation_job_dto import (
    TranslationJob,
    TranslationSourceCandidate,
)
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)
from app.services.translation_queue_service import (
    EnqueueResult,
    TranslationQueueService,
)


logger = get_logger(__name__)


class TranslationProductionResult(Enum):
    ENQUEUED = "enqueued"
    ALREADY_PENDING = "already_pending"
    FULL = "full"
    NOT_ACCEPTING = "not_accepting"
    INACTIVE_CHANNEL = "inactive_channel"
    SAME_LANGUAGE = "same_language"
    DELETED = "deleted"


class TranslationProducerService:
    """Create derived translation jobs without affecting raw message persistence."""

    def __init__(
        self,
        queue: TranslationQueueService,
        target_language: str,
        collection_channel_repository: CollectionChannelRepository | None = None,
    ):
        target_language = target_language.strip()
        if not target_language:
            raise ValueError("target_language must not be empty")
        self.queue = queue
        self.target_language = target_language
        self.collection_channel_repository = (
            collection_channel_repository
            if collection_channel_repository is not None
            else CollectionChannelRepository()
        )
        self._accepting = False

    @property
    def accepting(self) -> bool:
        return self._accepting

    def start(self) -> None:
        self._accepting = True

    def stop(self) -> None:
        self._accepting = False

    def enqueue_candidates(
        self,
        candidates: Iterable[TranslationSourceCandidate],
    ) -> dict[int, TranslationProductionResult]:
        candidates = tuple(candidates)
        if not self._accepting:
            return {
                candidate.message_id: TranslationProductionResult.NOT_ACCEPTING
                for candidate in candidates
            }

        enabled_channels_by_guild: dict[int, set[int]] = {}
        results: dict[int, TranslationProductionResult] = {}

        for candidate in candidates:
            if candidate.deleted_at is not None:
                results[candidate.message_id] = TranslationProductionResult.DELETED
                continue

            if (
                candidate.source_language.strip().casefold()
                == self.target_language.casefold()
            ):
                results[candidate.message_id] = (
                    TranslationProductionResult.SAME_LANGUAGE
                )
                continue

            enabled_channel_ids = enabled_channels_by_guild.get(candidate.guild_id)
            if enabled_channel_ids is None:
                enabled_channel_ids = set(
                    self.collection_channel_repository.get_enabled_channel_ids(
                        candidate.guild_id
                    )
                )
                enabled_channels_by_guild[candidate.guild_id] = enabled_channel_ids

            if candidate.channel_id not in enabled_channel_ids:
                results[candidate.message_id] = (
                    TranslationProductionResult.INACTIVE_CHANNEL
                )
                continue

            enqueue_result = self.queue.enqueue(TranslationJob(
                message_id=candidate.message_id,
                target_language=self.target_language,
                source_content_hash=candidate.source_content_hash,
            ))
            results[candidate.message_id] = TranslationProductionResult(
                enqueue_result.value
            )

            if enqueue_result is EnqueueResult.FULL:
                logger.warning(
                    "Translation queue full; skipped message #%s",
                    candidate.message_id,
                )

        return results
