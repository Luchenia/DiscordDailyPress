from collections import Counter

from app.dto.analysis_dataset_dto import AnalysisDatasetDTO
from app.dto.statistics_result_dto import (
    AuthorMessageCountDTO,
    ChannelMessageCountDTO,
    DailyMessageCountDTO,
    HourlyMessageCountDTO,
    StatisticsResultDTO,
)


class StatisticsService:
    """
    AnalysisDataset에서 통계 정보를 계산하는 Service
    """

    def analyze(
        self,
        dataset: AnalysisDatasetDTO,
    ) -> StatisticsResultDTO:

        author_counts = Counter(
            message.author_id
            for message in dataset.messages
        )

        channel_counts = Counter(
            message.channel_id
            for message in dataset.messages
        )

        daily_counts = Counter(
            message.created_at.date().isoformat()
            for message in dataset.messages
        )

        hourly_counts = Counter(
            message.created_at.hour
            for message in dataset.messages
        )

        author_names = {
            message.author_id: message.author_display_name
            for message in dataset.messages
        }

        channel_names = {
            message.channel_id: message.channel_name
            for message in dataset.messages
        }

        # ==========================
        # 평균 메시지 길이
        # ==========================

        if dataset.messages:

            total_message_length = sum(
                len(message.content)
                for message in dataset.messages
            )

            average_message_length = (
                total_message_length
                / len(dataset.messages)
            )

        else:

            average_message_length = 0.0

        # ==========================
        # 평균 일일 메시지 수
        # ==========================

        if daily_counts:

            average_daily_message_count = (
                dataset.metadata.message_count
                / len(daily_counts)
            )

        else:

            average_daily_message_count = 0.0

        # ==========================
        # 가장 활발한 시간대
        # ==========================

        if hourly_counts:

            peak_activity_hour = (
                hourly_counts.most_common(1)[0][0]
            )

        else:

            peak_activity_hour = None

        # ==========================
        # 가장 활발한 날짜
        # ==========================

        if daily_counts:

            peak_activity_date, peak_activity_date_count = (
                max(
                    daily_counts.items(),
                    key=lambda item: (
                        item[1],
                        item[0],
                    ),
                )
            )

        else:

            peak_activity_date = None
            peak_activity_date_count = 0

        # ==========================
        # 작성자 통계
        # ==========================

        top_authors = [
            AuthorMessageCountDTO(
                author_id=author_id,
                author_display_name=author_names[author_id],
                message_count=count,
            )
            for author_id, count in author_counts.most_common()
        ]

        # ==========================
        # 채널 통계
        # ==========================

        channel_activity = [
            ChannelMessageCountDTO(
                channel_id=channel_id,
                channel_name=channel_names[channel_id],
                message_count=count,
            )
            for channel_id, count in channel_counts.most_common()
        ]

        # ==========================
        # 일별 통계
        # ==========================

        daily_activity = [
            DailyMessageCountDTO(
                date=date,
                message_count=count,
            )
            for date, count in sorted(
                daily_counts.items()
            )
        ]

        # ==========================
        # 시간대별 통계
        # ==========================

        hourly_activity = [
            HourlyMessageCountDTO(
                hour=hour,
                message_count=count,
            )
            for hour, count in sorted(
                hourly_counts.items()
            )
        ]

        return StatisticsResultDTO(
            message_count=dataset.metadata.message_count,
            author_count=dataset.metadata.author_count,
            channel_count=dataset.metadata.channel_count,

            top_authors=top_authors,
            channel_activity=channel_activity,

            daily_activity=daily_activity,
            hourly_activity=hourly_activity,

            language_distribution=(
                dataset.metadata.language_distribution.copy()
            ),

            average_message_length=(
                average_message_length
            ),

            peak_activity_hour=(
                peak_activity_hour
            ),

            peak_activity_date=(
                peak_activity_date
            ),

            peak_activity_date_count=(
                peak_activity_date_count
            ),

            average_daily_message_count=(
                average_daily_message_count
            ),
        )