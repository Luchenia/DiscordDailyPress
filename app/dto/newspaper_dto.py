from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dto.analysis_text_dto import AnalysisTextSource


class NewspaperMessageProvenanceDTO(BaseModel):
    """Content-free source identity retained for newspaper auditing."""

    model_config = ConfigDict(frozen=True)

    message_id: int
    channel_id: int
    created_at_utc: datetime
    source_language: str
    analysis_language: str
    analysis_content_source: AnalysisTextSource
    source_content_hash: str
    translation_id: int | None = None


class NewspaperSectionDTO(BaseModel):
    """A deterministic topic section backed by validated summary evidence."""

    model_config = ConfigDict(frozen=True)

    section_number: int = Field(gt=0)
    topic_id: str = Field(min_length=1)
    label: str | None = None
    summary_text: str = Field(min_length=1)
    topic_message_count: int = Field(gt=0)
    evidence_message_ids: tuple[int, ...]
    evidence_message_count: int = Field(gt=0)
    source_messages: tuple[NewspaperMessageProvenanceDTO, ...]


class NewspaperEditionMetadataDTO(BaseModel):
    """Immutable analysis scope and KST-facing edition metadata."""

    model_config = ConfigDict(frozen=True)

    edition_date: date
    display_timezone: str
    guild_id: int
    channel_ids: tuple[int, ...]
    scope_start_at_utc: datetime
    scope_end_at_utc: datetime
    scope_start_at_kst: datetime
    scope_end_at_kst: datetime
    input_message_count: int = Field(ge=0)
    topic_count: int = Field(ge=0)
    unassigned_message_count: int = Field(ge=0)


class NewspaperResultDTO(BaseModel):
    """Provider-independent in-memory newspaper and rendered Markdown."""

    model_config = ConfigDict(frozen=True)

    edition: NewspaperEditionMetadataDTO
    output_language: str = Field(min_length=1)
    detector_id: str = Field(min_length=1)
    summarizer_id: str = Field(min_length=1)
    sections: tuple[NewspaperSectionDTO, ...]
    unassigned_messages: tuple[NewspaperMessageProvenanceDTO, ...]
    markdown_text: str = Field(min_length=1)
