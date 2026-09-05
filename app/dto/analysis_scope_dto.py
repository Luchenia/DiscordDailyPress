from datetime import datetime

from pydantic import BaseModel
from pydantic import field_validator

from app.utils.datetime_utils import ensure_utc


class AnalysisScopeDTO(BaseModel):
    """
    AI 분석에 사용할 데이터의 범위를 정의한다.
    """

    guild_id: int

    channel_ids: list[int]

    start_at: datetime

    end_at: datetime

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_datetime_to_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
