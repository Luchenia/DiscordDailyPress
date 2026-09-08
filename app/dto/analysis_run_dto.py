from pydantic import BaseModel, ConfigDict, Field

from app.dto.analysis_dataset_dto import AnalysisDatasetMetadataDTO
from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.topic_detection_dto import TopicDetectionMessageDTO
from app.dto.topic_summarization_dto import TopicSummaryDTO


class AnalysisRunLimitsDTO(BaseModel):
    """Explicit provider-neutral bounds supplied by an analysis-run caller."""

    model_config = ConfigDict(frozen=True)

    max_messages: int = Field(gt=0)
    max_total_characters: int = Field(gt=0)


class AnalysisRunRequestDTO(BaseModel):
    """Prepared-analysis request plus mandatory bounds for future AI calls."""

    model_config = ConfigDict(frozen=True)

    analysis_request: AnalysisRequestDTO
    limits: AnalysisRunLimitsDTO


class AnalysisRunResultDTO(BaseModel):
    """Provider-independent topic summaries ready for a future composer."""

    model_config = ConfigDict(frozen=True)

    scope: AnalysisScopeDTO
    detector_id: str
    summarizer_id: str
    output_language: str
    dataset_metadata: AnalysisDatasetMetadataDTO
    input_message_count: int
    input_analysis_character_count: int
    limits: AnalysisRunLimitsDTO
    summaries: tuple[TopicSummaryDTO, ...]
    unassigned_messages: tuple[TopicDetectionMessageDTO, ...]
