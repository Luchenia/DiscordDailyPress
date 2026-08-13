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

        top_authors = [
            AuthorMessageCountDTO(
                author_id=author_id,
                author_display_name=author_names[author_id],
                message_count=count,
            )
            for author_id, count in author_counts.most_common()
        ]

        channel_activity = [
            ChannelMessageCountDTO(
                channel_id=channel_id,
                channel_name=channel_names[channel_id],
                message_count=count,
            )
            for channel_id, count in channel_counts.most_common()
        ]

        daily_activity = [
            DailyMessageCountDTO(
                date=date,
                message_count=count,
            )
            for date, count in sorted(daily_counts.items())
        ]

        hourly_activity = [
            HourlyMessageCountDTO(
                hour=hour,
                message_count=count,
            )
            for hour, count in sorted(hourly_counts.items())
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
        )