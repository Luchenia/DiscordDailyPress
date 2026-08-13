from datetime import datetime, timezone

from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.services.analysis_service import AnalysisService
from app.services.statistics_service import StatisticsService


def main():
    analysis_service = AnalysisService()
    statistics_service = StatisticsService()

    scope = AnalysisScopeDTO(
        guild_id=1534142774847471716,
        channel_ids=[
            1534142775925145643,
        ],
        start_at=datetime(
            2026,
            8,
            1,
            tzinfo=timezone.utc,
        ),
        end_at=datetime.now(timezone.utc),
    )

    dataset = analysis_service.build_dataset(scope)

    statistics = statistics_service.analyze(dataset)

    print()
    print("========== Analysis Result ==========")

    print(f"Messages : {statistics.message_count}")
    print(f"Authors  : {statistics.author_count}")
    print(f"Channels : {statistics.channel_count}")

    print()
    print("----- Top Authors -----")

    for author in statistics.top_authors:
        print(
            f"{author.author_display_name}: "
            f"{author.message_count}"
        )

    print()
    print("----- Channel Activity -----")

    for channel in statistics.channel_activity:
        print(
            f"{channel.channel_name}: "
            f"{channel.message_count}"
        )

    print()
    print("----- Daily Activity -----")

    for daily in statistics.daily_activity:
        print(
            f"{daily.date}: "
            f"{daily.message_count}"
        )

    print()
    print("----- Hourly Activity -----")

    for hourly in statistics.hourly_activity:
        print(
            f"{hourly.hour:02d}:00 - "
            f"{hourly.message_count}"
        )

    print()
    print("----- Language Distribution -----")

    for language, ratio in (
        statistics.language_distribution.items()
    ):
        print(
            f"{language}: "
            f"{ratio:.2%}"
        )


if __name__ == "__main__":
    main()