from datetime import datetime, timezone

from app.dto.analysis_dataset_dto import (
    AnalysisDatasetDTO,
    AnalysisDatasetMetadataDTO,
)
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.statistics_result_dto import StatisticsResultDTO
from app.services.statistics_service import StatisticsService


def create_analysis_message(
    message_id: int,
    author_id: int,
    author_display_name: str,
    channel_id: int,
    channel_name: str,
    language: str,
) -> AnalysisMessageDTO:

    return AnalysisMessageDTO(
        message_id=message_id,

        guild_id=100,

        channel_id=channel_id,
        channel_name=channel_name,

        author_id=author_id,
        author_display_name=author_display_name,

        content="테스트 메시지",
        language=language,

        created_at=datetime.now(timezone.utc),
    )


def create_dataset() -> AnalysisDatasetDTO:

    messages = [
        create_analysis_message(
            message_id=1,
            author_id=1,
            author_display_name="M.K",
            channel_id=10,
            channel_name="일반",
            language="ko",
        ),
        create_analysis_message(
            message_id=2,
            author_id=1,
            author_display_name="M.K",
            channel_id=10,
            channel_name="일반",
            language="ko",
        ),
        create_analysis_message(
            message_id=3,
            author_id=2,
            author_display_name="철수",
            channel_id=10,
            channel_name="일반",
            language="ko",
        ),
        create_analysis_message(
            message_id=4,
            author_id=2,
            author_display_name="철수",
            channel_id=20,
            channel_name="잡담",
            language="en",
        ),
        create_analysis_message(
            message_id=5,
            author_id=3,
            author_display_name="영희",
            channel_id=20,
            channel_name="잡담",
            language="ko",
        ),
    ]

    metadata = AnalysisDatasetMetadataDTO(
        message_count=5,
        author_count=3,
        channel_count=2,
        language_distribution={
            "ko": 0.8,
            "en": 0.2,
        },
    )

    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        end_at=datetime(2026, 8, 2, tzinfo=timezone.utc),
    )

    return AnalysisDatasetDTO(
        scope=scope,
        messages=messages,
        metadata=metadata,
    )


def test_statistics_service_counts_authors_and_channels():

    service = StatisticsService()

    dataset = create_dataset()

    result = service.analyze(dataset)

    assert isinstance(result, StatisticsResultDTO)

    assert result.message_count == 5
    assert result.author_count == 3
    assert result.channel_count == 2

    assert result.top_authors[0].author_id == 1
    assert result.top_authors[0].author_display_name == "M.K"
    assert result.top_authors[0].message_count == 2

    assert result.top_authors[1].author_id == 2
    assert result.top_authors[1].message_count == 2

    assert result.top_authors[2].author_id == 3
    assert result.top_authors[2].message_count == 1

    assert result.channel_activity[0].channel_id == 10
    assert result.channel_activity[0].channel_name == "일반"
    assert result.channel_activity[0].message_count == 3

    assert result.channel_activity[1].channel_id == 20
    assert result.channel_activity[1].channel_name == "잡담"
    assert result.channel_activity[1].message_count == 2

    assert result.language_distribution == {
        "ko": 0.8,
        "en": 0.2,
    }

def test_statistics_service_counts_daily_and_hourly_activity():

    service = StatisticsService()

    dataset = create_dataset()

    base_time = datetime(
        2026,
        8,
        1,
        10,
        tzinfo=timezone.utc,
    )

    dataset.messages[0].created_at = base_time
    dataset.messages[1].created_at = base_time.replace(
        hour=10,
        minute=30,
    )
    dataset.messages[2].created_at = base_time.replace(
        hour=15,
    )
    dataset.messages[3].created_at = base_time.replace(
        day=2,
        hour=10,
    )
    dataset.messages[4].created_at = base_time.replace(
        day=2,
        hour=20,
    )

    result = service.analyze(dataset)

    assert result.daily_activity[0].date == "2026-08-01"
    assert result.daily_activity[0].message_count == 3

    assert result.daily_activity[1].date == "2026-08-02"
    assert result.daily_activity[1].message_count == 2

    assert result.hourly_activity[0].hour == 10
    assert result.hourly_activity[0].message_count == 3

    assert result.hourly_activity[1].hour == 15
    assert result.hourly_activity[1].message_count == 1

    assert result.hourly_activity[2].hour == 20
    assert result.hourly_activity[2].message_count == 1