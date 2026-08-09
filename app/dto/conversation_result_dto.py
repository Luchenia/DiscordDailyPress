from datetime import datetime

from pydantic import BaseModel


class ConversationResultDTO(BaseModel):
    """
    종료된 Conversation Session의 처리 결과
    """

    message_ids: list[int]

    author_id: int
    channel_id: int

    text: str
    language: str

    started_at: datetime
    ended_at: datetime