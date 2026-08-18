from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.dto.analysis_request_dto import AnalysisRequestDTO


def test_analysis_request_creates_successfully():
    request = AnalysisRequestDTO(
        guild_id=100,
        start_at=datetime(
            2026,
            2,
            17,
            tzinfo=timezone.utc,
        ),
        end_at=datetime(
            2026,
            8,
            17,
            tzinfo=timezone.utc,
        ),
        output_language="ko",
    )

    assert request.guild_id == 100
    assert request.start_at == datetime(
        2026,
        2,
        17,
        tzinfo=timezone.utc,
    )
    assert request.end_at == datetime(
        2026,
        8,
        17,
        tzinfo=timezone.utc,
    )
    assert request.output_language == "ko"


def test_analysis_request_rejects_invalid_guild_id():
    with pytest.raises(ValidationError):
        AnalysisRequestDTO(
            guild_id="abc",
            start_at=datetime(
                2026,
                2,
                17,
                tzinfo=timezone.utc,
            ),
            end_at=datetime(
                2026,
                8,
                17,
                tzinfo=timezone.utc,
            ),
            output_language="ko",
        )


def test_analysis_request_rejects_when_start_at_is_after_end_at():
    with pytest.raises(ValidationError):
        AnalysisRequestDTO(
            guild_id=100,
            start_at=datetime(
                2026,
                8,
                17,
                tzinfo=timezone.utc,
            ),
            end_at=datetime(
                2026,
                2,
                17,
                tzinfo=timezone.utc,
            ),
            output_language="ko",
        )


def test_analysis_request_rejects_when_start_at_equals_end_at():
    with pytest.raises(ValidationError):
        AnalysisRequestDTO(
            guild_id=100,
            start_at=datetime(
                2026,
                8,
                17,
                tzinfo=timezone.utc,
            ),
            end_at=datetime(
                2026,
                8,
                17,
                tzinfo=timezone.utc,
            ),
            output_language="ko",
        )