from datetime import datetime

from pydantic import BaseModel


class AnalysisScopeDTO(BaseModel):
    """
    AI 분석에 사용할 데이터의 범위를 정의한다.
    """

    guild_id: int

    channel_ids: list[int]

    start_at: datetime

    end_at: datetime