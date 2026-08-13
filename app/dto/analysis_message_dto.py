from datetime import datetime

from pydantic import BaseModel


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
    language: str

    created_at: datetime