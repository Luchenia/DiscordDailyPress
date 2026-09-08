from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.utils.datetime_utils import ensure_utc


class TopicDetectionMessageDTO(BaseModel):
    """Prepared analysis input with source and translation provenance."""

    model_config = ConfigDict(frozen=True)

    message_id: int
    guild_id: int
    channel_id: int
    channel_name: str
    author_id: int
    author_display_name: str
    analysis_content: str
    analysis_language: str
    source_language: str
    analysis_content_source: AnalysisTextSource
    source_content_hash: str
    translation_id: int | None = None
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_datetime_to_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def validate_translation_provenance(self):
        if (
            self.analysis_content_source is AnalysisTextSource.TRANSLATION
            and self.translation_id is None
        ):
            raise ValueError("translated topic input requires translation_id")
        if (
            self.analysis_content_source is AnalysisTextSource.RAW
            and self.translation_id is not None
        ):
            raise ValueError("raw topic input cannot reference translation_id")
        return self


class TopicCandidateDTO(BaseModel):
    """Provider proposal using only Chronicle message identities."""

    topic_id: str
    label: str | None = None
    message_ids: list[int]

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("topic_id must not be empty")
        return value

    @model_validator(mode="after")
    def validate_members(self):
        if not self.message_ids:
            raise ValueError("topic candidate must contain at least one message")
        if len(self.message_ids) != len(set(self.message_ids)):
            raise ValueError("topic candidate contains duplicate message IDs")
        return self


class TopicDetectionProposalDTO(BaseModel):
    """Provider output before Chronicle validates and materializes membership."""

    topics: list[TopicCandidateDTO]
    unassigned_message_ids: list[int]


class TopicMembershipDTO(BaseModel):
    topic_id: str
    message: TopicDetectionMessageDTO


class DetectedTopicDTO(BaseModel):
    topic_id: str
    label: str | None = None
    memberships: list[TopicMembershipDTO]


class TopicDetectionResultDTO(BaseModel):
    scope: AnalysisScopeDTO
    detector_id: str
    topics: list[DetectedTopicDTO]
    unassigned_messages: list[TopicDetectionMessageDTO]
