from collections import Counter

from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_dataset_dto import (
    AnalysisDatasetDTO,
    AnalysisDatasetMetadataDTO,
)
from app.dto.statistics_result_dto import StatisticsResultDTO
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.services.analysis_scope_resolver import AnalysisScopeResolver
from app.services.statistics_service import StatisticsService


class AnalysisService:
    """
    분석 범위에 해당하는 데이터를 조회하는 Service
    """

    def __init__(
        self,
        repository: MessageRepository | None = None,
        scope_resolver: AnalysisScopeResolver | None = None,
        statistics_service: StatisticsService | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else MessageRepository()
        )

        self.scope_resolver = (
            scope_resolver
            if scope_resolver is not None
            else AnalysisScopeResolver()
        )

        self.statistics_service = (
            statistics_service
            if statistics_service is not None
            else StatisticsService()
        )

    def analyze(
        self,
        request: AnalysisRequestDTO,
    ) -> StatisticsResultDTO:

        scope = self.scope_resolver.resolve(
            request,
        )

        dataset = self.build_dataset(
            scope,
        )

        return self.statistics_service.analyze(
            dataset,
        )

    def get_messages(
        self,
        scope: AnalysisScopeDTO,
    ) -> list[Message]:

        return self.repository.get_by_analysis_scope(
            guild_id=scope.guild_id,
            channel_ids=scope.channel_ids,
            start_at=scope.start_at,
            end_at=scope.end_at,
        )

    def to_analysis_message(
        self,
        message: Message,
    ) -> AnalysisMessageDTO:

        return AnalysisMessageDTO(
            message_id=message.discord_message_id,

            guild_id=message.guild_id,

            channel_id=message.channel_id,
            channel_name=message.channel_name,

            author_id=message.author_id,
            author_display_name=message.author_display_name,

            content=message.content,
            language=message.language,

            created_at=message.created_at,
        )

    def build_dataset(
        self,
        scope: AnalysisScopeDTO,
    ) -> AnalysisDatasetDTO:

        messages = self.get_messages(scope)

        analysis_messages = [
            self.to_analysis_message(message)
            for message in messages
        ]

        message_count = len(analysis_messages)

        author_count = len({
            message.author_id
            for message in analysis_messages
        })

        channel_count = len({
            message.channel_id
            for message in analysis_messages
        })

        language_counts = Counter(
            message.language
            for message in analysis_messages
        )

        language_distribution = {}

        if message_count > 0:
            language_distribution = {
                language: count / message_count
                for language, count in language_counts.items()
            }

        metadata = AnalysisDatasetMetadataDTO(
            message_count=message_count,
            author_count=author_count,
            channel_count=channel_count,
            language_distribution=language_distribution,
        )

        return AnalysisDatasetDTO(
            scope=scope,
            messages=analysis_messages,
            metadata=metadata,
        )