from datetime import datetime

from pydantic import BaseModel
from pydantic import field_validator

from app.dto.analysis_text_dto import AnalysisTextSource
from app.utils.datetime_utils import ensure_utc


class AnalysisMessageDTO(BaseModel):
    """
    AI 분석을 위해 가공된 Discord 메시지 데이터
    """

    message_id: int

    guild_id: int

    channel_id: int
    channel_name: str

    author_id: int
    author_display_name: str

    content: str
    # Detected language of the message's raw source content.
    language: str

    # Text selected for downstream AI analysis. Raw fields above remain available
    # for statistics, provenance, and source-of-truth access.
    analysis_content: str
    analysis_language: str
    analysis_content_source: AnalysisTextSource
    source_content_hash: str
    translation_id: int | None = None

    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def normalize_datetime_to_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
