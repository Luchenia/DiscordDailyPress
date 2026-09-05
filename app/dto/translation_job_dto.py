from dataclasses import dataclass


@dataclass(frozen=True)
class TranslationJob:
    """Translation key; message_id is messages.id, never a Discord ID."""

    message_id: int
    target_language: str
    source_content_hash: str

    @property
    def key(self) -> tuple[int, str, str]:
        return (self.message_id, self.target_language, self.source_content_hash)
