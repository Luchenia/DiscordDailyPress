from typing import Protocol

from app.dto.topic_detection_dto import (
    TopicDetectionMessageDTO,
    TopicDetectionProposalDTO,
)


class TopicDetectionProvider(Protocol):
    """Pluggable grouping policy; provider selection and tuning remain external."""

    detector_id: str

    async def detect_topics(
        self,
        messages: tuple[TopicDetectionMessageDTO, ...],
    ) -> TopicDetectionProposalDTO: ...
