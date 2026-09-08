from enum import Enum

from pydantic import BaseModel, model_validator


class AnalysisTextSource(str, Enum):
    RAW = "raw"
    TRANSLATION = "translation"


class ResolvedAnalysisTextDTO(BaseModel):
    """Text selected for analysis plus its current-source provenance."""

    content: str
    language: str
    source_language: str
    content_source: AnalysisTextSource
    source_content_hash: str
    translation_id: int | None = None

    @model_validator(mode="after")
    def validate_translation_provenance(self):
        if (
            self.content_source is AnalysisTextSource.TRANSLATION
            and self.translation_id is None
        ):
            raise ValueError("translated analysis text requires translation_id")
        if (
            self.content_source is AnalysisTextSource.RAW
            and self.translation_id is not None
        ):
            raise ValueError("raw analysis text cannot reference translation_id")
        return self
