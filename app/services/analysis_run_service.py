import asyncio

from app.dto.analysis_run_dto import (
    AnalysisRunRequestDTO,
    AnalysisRunResultDTO,
)
from app.services.analysis_service import AnalysisService
from app.services.topic_detection_service import TopicDetectionService
from app.services.topic_summarization_service import TopicSummarizationService


class AnalysisRunContractError(ValueError):
    """Raised when an analysis run request cannot safely reach providers."""


class AnalysisRunLimitError(AnalysisRunContractError):
    """Raised before provider invocation when explicit input bounds are exceeded."""


class AnalysisRunService:
    """Compose prepared analysis, topic detection, and topic summarization."""

    def __init__(
        self,
        analysis_service: AnalysisService,
        topic_detection_service: TopicDetectionService,
        topic_summarization_service: TopicSummarizationService,
    ):
        self.analysis_service = analysis_service
        self.topic_detection_service = topic_detection_service
        self.topic_summarization_service = topic_summarization_service

    async def run(
        self,
        request: AnalysisRunRequestDTO,
    ) -> AnalysisRunResultDTO:
        output_language = request.analysis_request.output_language.strip()
        if not output_language:
            raise AnalysisRunContractError(
                "output_language must not be empty"
            )

        analysis_request = request.analysis_request.model_copy(
            update={"output_language": output_language}
        )
        dataset = await asyncio.to_thread(
            self.analysis_service.prepare_dataset,
            analysis_request,
        )

        input_message_count = len(dataset.messages)
        input_analysis_character_count = sum(
            len(message.analysis_content)
            for message in dataset.messages
        )
        self._validate_limits(
            input_message_count,
            input_analysis_character_count,
            request,
        )

        detected = await self.topic_detection_service.detect_topics(dataset)
        summarized = await self.topic_summarization_service.summarize_topics(
            detected,
            output_language,
        )

        return AnalysisRunResultDTO(
            scope=summarized.scope,
            detector_id=summarized.detector_id,
            summarizer_id=summarized.summarizer_id,
            output_language=summarized.output_language,
            dataset_metadata=dataset.metadata,
            input_message_count=input_message_count,
            input_analysis_character_count=input_analysis_character_count,
            limits=request.limits,
            summaries=summarized.summaries,
            unassigned_messages=summarized.unassigned_messages,
        )

    @staticmethod
    def _validate_limits(
        message_count: int,
        total_characters: int,
        request: AnalysisRunRequestDTO,
    ) -> None:
        if message_count > request.limits.max_messages:
            raise AnalysisRunLimitError(
                "analysis message count exceeds the requested limit: "
                f"{message_count} > {request.limits.max_messages}"
            )
        if total_characters > request.limits.max_total_characters:
            raise AnalysisRunLimitError(
                "analysis character count exceeds the requested limit: "
                f"{total_characters} > "
                f"{request.limits.max_total_characters}"
            )
