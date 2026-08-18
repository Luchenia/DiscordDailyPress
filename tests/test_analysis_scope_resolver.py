from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.services.analysis_scope_resolver import AnalysisScopeResolver


def create_request(
    guild_id: int = 100,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> AnalysisRequestDTO:

    if start_at is None:
        start_at = datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        )

    if end_at is None:
        end_at = datetime(
            2026,
            8,
            14,
            tzinfo=timezone.utc,
        )

    return AnalysisRequestDTO(
        guild_id=guild_id,
        start_at=start_at,
        end_at=end_at,
        output_language="ko",
    )


def test_resolver_creates_scope_from_enabled_channels():
    repository = Mock()

    repository.get_enabled_channel_ids.return_value = [
        10,
        20,
    ]

    resolver = AnalysisScopeResolver(
        repository=repository,
    )

    request = create_request()

    result = resolver.resolve(request)

    assert isinstance(result, AnalysisScopeDTO)

    assert result.guild_id == 100
    assert result.channel_ids == [10, 20]
    assert result.start_at == request.start_at
    assert result.end_at == request.end_at

    repository.get_enabled_channel_ids.assert_called_once_with(
        100,
    )


def test_resolver_excludes_disabled_channels():
    repository = Mock()

    repository.get_enabled_channel_ids.return_value = [
        10,
        30,
    ]

    resolver = AnalysisScopeResolver(
        repository=repository,
    )

    request = create_request()

    result = resolver.resolve(request)

    assert result.channel_ids == [10, 30]


def test_resolver_uses_request_guild_id():
    repository = Mock()

    repository.get_enabled_channel_ids.return_value = [
        50,
    ]

    resolver = AnalysisScopeResolver(
        repository=repository,
    )

    request = create_request(
        guild_id=999,
    )

    result = resolver.resolve(request)

    assert result.guild_id == 999

    repository.get_enabled_channel_ids.assert_called_once_with(
        999,
    )


def test_resolver_preserves_request_period():
    repository = Mock()

    repository.get_enabled_channel_ids.return_value = [
        10,
    ]

    resolver = AnalysisScopeResolver(
        repository=repository,
    )

    start_at = datetime(
        2026,
        7,
        1,
        12,
        30,
        tzinfo=timezone.utc,
    )

    end_at = datetime(
        2026,
        7,
        10,
        18,
        45,
        tzinfo=timezone.utc,
    )

    request = create_request(
        start_at=start_at,
        end_at=end_at,
    )

    result = resolver.resolve(request)

    assert result.start_at == start_at
    assert result.end_at == end_at


def test_resolver_rejects_when_no_enabled_channels():
    repository = Mock()

    repository.get_enabled_channel_ids.return_value = []

    resolver = AnalysisScopeResolver(
        repository=repository,
    )

    request = create_request()

    with pytest.raises(ValueError):
        resolver.resolve(request)