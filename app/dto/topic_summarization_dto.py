from pydantic import BaseModel, ConfigDict

from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.topic_detection_dto import TopicDetectionMessageDTO


class TopicSummarizationInputDTO(BaseModel):
    """Immutable prepared topic input exposed to a summarization provider."""

    model_config = ConfigDict(frozen=True)

    topic_id: str
    label: str | None = None
    messages: tuple[TopicDetectionMessageDTO, ...]
    output_language: str


class TopicSummaryCandidateDTO(BaseModel):
    """Untrusted provider proposal validated by TopicSummarizationService."""

    topic_id: str
    summary_text: str
    evidence_message_ids: list[int]


class TopicSummarizationProposalDTO(BaseModel):
    """Provider output before Chronicle validates topic and evidence identity."""

    summaries: list[TopicSummaryCandidateDTO]


class TopicSummaryDTO(BaseModel):
    """Validated topic summary retaining all prepared source provenance."""

    model_config = ConfigDict(frozen=True)

    topic_id: str
    label: str | None = None
    summary_text: str
    messages: tuple[TopicDetectionMessageDTO, ...]
    evidence_message_ids: tuple[int, ...]


class TopicSummarizationResultDTO(BaseModel):
    """Validated summaries plus complete analysis and detector provenance."""

    model_config = ConfigDict(frozen=True)

    scope: AnalysisScopeDTO
    detector_id: str
    summarizer_id: str
    output_language: str
    summaries: tuple[TopicSummaryDTO, ...]
    unassigned_messages: tuple[TopicDetectionMessageDTO, ...]
