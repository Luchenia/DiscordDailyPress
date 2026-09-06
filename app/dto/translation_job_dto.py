from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TranslationJob:
    """Translation key; message_id is messages.id, never a Discord ID."""

    message_id: int
    target_language: str
    source_content_hash: str

    @property
    def key(self) -> tuple[int, str, str]:
        return (self.message_id, self.target_language, self.source_content_hash)


@dataclass(frozen=True)
class TranslationSourceCandidate:
    """Plain source metadata captured before a committed enqueue attempt."""

    message_id: int
    guild_id: int
    channel_id: int
    source_language: str
    source_content_hash: str
    deleted_at: datetime | None
