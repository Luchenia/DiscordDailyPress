from collections.abc import Sequence

from app.services.translation_output_integrity import (
    TranslationIntegrityError,
    TranslationOutputIntegrityValidator,
)
from app.services.translation_provider import (
    TranslationProvider,
    TranslationProviderError,
)


class FallbackTranslationProvider:
    """Try each provider once, accepting only output that preserves source tokens."""

    def __init__(
        self,
        providers: Sequence[TranslationProvider],
        validator: TranslationOutputIntegrityValidator | None = None,
    ):
        if not providers:
            raise ValueError("at least one translation provider is required")
        self.providers = tuple(providers)
        self.validator = validator or TranslationOutputIntegrityValidator()

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        failures: list[TranslationProviderError] = []

        for provider in self.providers:
            try:
                translated_text = await provider.translate(
                    text,
                    source_language,
                    target_language,
                )
            except TranslationProviderError as error:
                failures.append(error)
                continue

            try:
                self.validator.validate(text, translated_text)
            except TranslationIntegrityError as error:
                failures.append(error)
                continue

            return translated_text

        error = TranslationProviderError(
            "All configured translation providers failed",
            retryable=any(failure.retryable for failure in failures),
        )
        raise error from failures[-1]
