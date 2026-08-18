from datetime import datetime

from pydantic import BaseModel, model_validator


class AnalysisRequestDTO(BaseModel):
    guild_id: int

    start_at: datetime
    end_at: datetime

    output_language: str

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_at >= self.end_at:
            raise ValueError(
                "start_at must be earlier than end_at"
            )

        return self