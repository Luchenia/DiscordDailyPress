from datetime import datetime, timezone
from unittest.mock import Mock

from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.statistics_result_dto import StatisticsResultDTO
from app.services.analysis_scope_resolver import AnalysisScopeResolver
from app.services.analysis_service import AnalysisService
from app.services.statistics_service import StatisticsService


def create_request() -> AnalysisRequestDTO:

    return AnalysisRequestDTO(
        guild_id=100,
        start_at=datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        ),
        end_at=datetime(
            2026,
            8,
            14,
            tzinfo=timezone.utc,
        ),
        output_language="ko",
    )


def test_analysis_flow_connects_request_to_statistics():

    scope_resolver = Mock(
        spec=AnalysisScopeResolver,
    )

    statistics_service = Mock(
        spec=StatisticsService,
    )

    service = AnalysisService()

    service.scope_resolver = scope_resolver
    service.statistics_service = statistics_service

    request = create_request()

    scope = Mock()
    dataset = Mock()

    expected_result = StatisticsResultDTO(
        message_count=10,
        author_count=2,
        channel_count=2,
        top_authors=[],
        channel_activity=[],
        language_distribution={},
        daily_activity=[],
        hourly_activity=[],
        average_message_length=0.0,
        peak_activity_hour=None,
        peak_activity_date=None,
        peak_activity_date_count=0,
    )

    scope_resolver.resolve.return_value = scope

    statistics_service.analyze.return_value = (
        expected_result
    )

    service.build_dataset = Mock(
        return_value=dataset,
    )

    result = service.analyze(
        request,
    )

    assert result is expected_result

    scope_resolver.resolve.assert_called_once_with(
        request,
    )

    service.build_dataset.assert_called_once_with(
        scope,
        output_language="ko",
    )

    statistics_service.analyze.assert_called_once_with(
        dataset,
    )


def test_analysis_flow_does_not_call_statistics_when_dataset_creation_fails():

    scope_resolver = Mock(
        spec=AnalysisScopeResolver,
    )

    statistics_service = Mock(
        spec=StatisticsService,
    )

    service = AnalysisService()

    service.scope_resolver = scope_resolver
    service.statistics_service = statistics_service

    request = create_request()

    scope = Mock()

    scope_resolver.resolve.return_value = scope

    service.build_dataset = Mock(
        side_effect=ValueError(
            "분석 데이터를 생성할 수 없습니다."
        ),
    )

    try:

        service.analyze(
            request,
        )

    except ValueError:

        pass

    scope_resolver.resolve.assert_called_once_with(
        request,
    )

    service.build_dataset.assert_called_once_with(
        scope,
        output_language="ko",
    )

    statistics_service.analyze.assert_not_called()
