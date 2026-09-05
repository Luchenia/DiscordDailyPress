from typing import Protocol


class TranslationProvider(Protocol):
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate without blocking the event loop; implementations are injected."""
        ...
