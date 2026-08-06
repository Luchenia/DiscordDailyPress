from datetime import datetime

from pydantic import BaseModel


class DiscordMessageDTO(BaseModel):
    guild_id: int

    channel_id: int

    author_id: int

    author_name: str

    content: str

    created_at: datetime