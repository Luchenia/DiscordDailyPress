from collections.abc import Sequence
from typing import Protocol

from app.dto.analysis_text_dto import (
    AnalysisTextSource,
    ResolvedAnalysisTextDTO,
)
from app.models.message import Message
from app.repositories.message_translation_repository import (
    MessageTranslationRepository,
)
from app.utils.content_hash import calculate_source_content_hash


def normalize_source_language(language: str | None) -> str:
    """Apply the existing unknown-language contract without mutating storage."""
    if language is None or not language.strip():
        return "unknown"
    return language.strip()


class MissingTranslationPolicy(Protocol):
    def resolve(
        self,
        message: Message,
        target_language: str,
        source_content_hash: str,
    ) -> ResolvedAnalysisTextDTO: ...


class RawSourceFallbackPolicy:
    """Keep analysis available when a current translation is unavailable."""

    def resolve(
        self,
        message: Message,
        target_language: str,
        source_content_hash: str,
    ) -> ResolvedAnalysisTextDTO:
        source_language = normalize_source_language(message.language)
        return ResolvedAnalysisTextDTO(
            content=message.content,
            language=source_language,
            source_language=source_language,
            content_source=AnalysisTextSource.RAW,
            source_content_hash=source_content_hash,
        )


class AnalysisTextResolver:
    """Resolve raw or current translated text without producing translations."""

    def __init__(
        self,
        repository: MessageTranslationRepository | None = None,
        missing_translation_policy: MissingTranslationPolicy | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else MessageTranslationRepository()
        )
        self.missing_translation_policy = (
            missing_translation_policy or RawSourceFallbackPolicy()
        )

    def resolve_many(
        self,
        messages: Sequence[Message],
        target_language: str,
    ) -> list[ResolvedAnalysisTextDTO]:
        target_language = target_language.strip()
        if not target_language:
            raise ValueError("target_language must not be empty")
        if any(message.deleted_at is not None for message in messages):
            raise ValueError("deleted messages are not eligible for analysis")

        source_hashes = [
            calculate_source_content_hash(message.content)
            for message in messages
        ]
        source_languages = [
            normalize_source_language(message.language)
            for message in messages
        ]
        translation_candidates = {
            message.id: source_hash
            for message, source_hash, source_language in zip(
                messages,
                source_hashes,
                source_languages,
                strict=True,
            )
            if (
                message.id is not None
                and source_language.casefold() != target_language.casefold()
            )
        }
        current_translations = (
            self.repository.get_current_batch(
                translation_candidates,
                target_language,
            )
            if translation_candidates
            else {}
        )

        resolved = []
        for message, source_hash, source_language in zip(
            messages,
            source_hashes,
            source_languages,
            strict=True,
        ):
            if source_language.casefold() == target_language.casefold():
                resolved.append(self._raw(
                    message,
                    source_hash,
                    source_language,
                ))
                continue

            translation = current_translations.get(message.id)
            if translation is None or not translation.translated_content.strip():
                resolved.append(self.missing_translation_policy.resolve(
                    message,
                    target_language,
                    source_hash,
                ))
                continue

            resolved.append(ResolvedAnalysisTextDTO(
                content=translation.translated_content,
                language=target_language,
                source_language=source_language,
                content_source=AnalysisTextSource.TRANSLATION,
                source_content_hash=source_hash,
                translation_id=translation.id,
            ))

        return resolved

    @staticmethod
    def _raw(
        message: Message,
        source_content_hash: str,
        source_language: str,
    ) -> ResolvedAnalysisTextDTO:
        return ResolvedAnalysisTextDTO(
            content=message.content,
            language=source_language,
            source_language=source_language,
            content_source=AnalysisTextSource.RAW,
            source_content_hash=source_content_hash,
        )
