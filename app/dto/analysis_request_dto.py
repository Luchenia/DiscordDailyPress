from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from app.utils.datetime_utils import ensure_utc


class AnalysisRequestDTO(BaseModel):
    guild_id: int

    start_at: datetime
    end_at: datetime

    output_language: str

    @field_validator("start_at", "end_at")
    @classmethod
    def normalize_datetime_to_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at >= self.end_at:
            raise ValueError(
                "start_at must be earlier than end_at"
            )

        return self
