from datetime import datetime

from pydantic import BaseModel
from pydantic import field_validator

from app.utils.datetime_utils import ensure_utc


class DiscordMessageDTO(BaseModel):

    # Discord 원본
    discord_message_id: int

    guild_id: int
    guild_name: str

    channel_id: int
    channel_name: str

    # 작성자
    author_id: int
    author_username: str
    author_display_name: str

    is_bot: bool

    # 메시지
    content: str

    # 첨부파일
    has_attachment: bool
    attachment_count: int

    # 답글
    reply_to_message_id: int | None = None

    # 시간
    created_at: datetime
    edited_at: datetime | None = None

    @field_validator("created_at", "edited_at")
    @classmethod
    def normalize_datetime_to_utc(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is None:
            return None

        return ensure_utc(value)
