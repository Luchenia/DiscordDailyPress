from typing import Protocol

from app.dto.topic_summarization_dto import (
    TopicSummarizationInputDTO,
    TopicSummarizationProposalDTO,
)


class TopicSummarizationProvider(Protocol):
    """Pluggable async summarizer; provider and model selection stay external."""

    summarizer_id: str

    async def summarize_topics(
        self,
        topics: tuple[TopicSummarizationInputDTO, ...],
    ) -> TopicSummarizationProposalDTO: ...
