from collections import Counter

from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_text_dto import (
    AnalysisTextSource,
    ResolvedAnalysisTextDTO,
)
from app.dto.analysis_dataset_dto import (
    AnalysisDatasetDTO,
    AnalysisDatasetMetadataDTO,
)
from app.dto.statistics_result_dto import StatisticsResultDTO
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.services.analysis_scope_resolver import AnalysisScopeResolver
from app.services.analysis_text_resolver import AnalysisTextResolver
from app.services.analysis_text_resolver import normalize_source_language
from app.services.statistics_service import StatisticsService
from app.utils.content_hash import calculate_source_content_hash


class AnalysisService:
    """
    분석 범위에 해당하는 데이터를 조회하는 Service
    """

    def __init__(
        self,
        repository: MessageRepository | None = None,
        scope_resolver: AnalysisScopeResolver | None = None,
        statistics_service: StatisticsService | None = None,
        text_resolver: AnalysisTextResolver | None = None,
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

        self.text_resolver = (
            text_resolver
            if text_resolver is not None
            else AnalysisTextResolver()
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
            output_language=request.output_language,
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
        resolved_text: ResolvedAnalysisTextDTO | None = None,
    ) -> AnalysisMessageDTO:

        if resolved_text is None:
            source_language = normalize_source_language(message.language)
            resolved_text = ResolvedAnalysisTextDTO(
                content=message.content,
                language=source_language,
                source_language=source_language,
                content_source=AnalysisTextSource.RAW,
                source_content_hash=calculate_source_content_hash(message.content),
            )

        return AnalysisMessageDTO(
            message_id=message.discord_message_id,

            guild_id=message.guild_id,

            channel_id=message.channel_id,
            channel_name=message.channel_name,

            author_id=message.author_id,
            author_display_name=message.author_display_name,

            content=message.content,
            language=resolved_text.source_language,

            analysis_content=resolved_text.content,
            analysis_language=resolved_text.language,
            analysis_content_source=resolved_text.content_source,
            source_content_hash=resolved_text.source_content_hash,
            translation_id=resolved_text.translation_id,

            created_at=message.created_at,
        )

    def build_dataset(
        self,
        scope: AnalysisScopeDTO,
        output_language: str | None = None,
    ) -> AnalysisDatasetDTO:

        messages = [
            message
            for message in self.get_messages(scope)
            if message.deleted_at is None
        ]

        resolved_texts = (
            self.text_resolver.resolve_many(messages, output_language)
            if output_language is not None
            else [None] * len(messages)
        )

        analysis_messages = [
            self.to_analysis_message(message, resolved_text)
            for message, resolved_text in zip(
                messages,
                resolved_texts,
                strict=True,
            )
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
