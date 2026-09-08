import asyncio
from datetime import UTC, datetime, timedelta
from threading import get_ident

import pytest
from pydantic import ValidationError

from app.dto.analysis_dataset_dto import (
    AnalysisDatasetDTO,
    AnalysisDatasetMetadataDTO,
)
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_run_dto import (
    AnalysisRunLimitsDTO,
    AnalysisRunRequestDTO,
)
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.dto.topic_detection_dto import (
    TopicCandidateDTO,
    TopicDetectionProposalDTO,
)
from app.dto.topic_summarization_dto import (
    TopicSummarizationProposalDTO,
    TopicSummaryCandidateDTO,
)
from app.services.analysis_run_service import (
    AnalysisRunContractError,
    AnalysisRunLimitError,
    AnalysisRunService,
)
from app.services.topic_detection_service import (
    TopicDetectionContractError,
    TopicDetectionService,
)
from app.services.topic_summarization_service import (
    TopicSummarizationContractError,
    TopicSummarizationService,
)
from app.utils.content_hash import calculate_source_content_hash


class FakeAnalysisService:
    def __init__(self, dataset: AnalysisDatasetDTO):
        self.dataset = dataset
        self.calls = []
        self.thread_id = None

    def prepare_dataset(self, request: AnalysisRequestDTO) -> AnalysisDatasetDTO:
        self.calls.append(request)
        self.thread_id = get_ident()
        return self.dataset


class FakeTopicDetectionProvider:
    detector_id = "fake-topic-detector:v1"

    def __init__(self, proposal: TopicDetectionProposalDTO):
        self.proposal = proposal
        self.calls = []

    async def detect_topics(self, messages):
        self.calls.append(messages)
        return self.proposal


class FakeTopicSummarizationProvider:
    summarizer_id = "fake-topic-summarizer:v1"

    def __init__(self, proposal: TopicSummarizationProposalDTO):
        self.proposal = proposal
        self.calls = []

    async def summarize_topics(self, topics):
        self.calls.append(topics)
        return self.proposal


def make_message(
    message_id: int,
    *,
    raw_content: str,
    analysis_content: str,
    created_at: datetime,
    source_language: str = "ko",
    content_source: AnalysisTextSource = AnalysisTextSource.RAW,
    translation_id: int | None = None,
) -> AnalysisMessageDTO:
    return AnalysisMessageDTO(
        message_id=message_id,
        guild_id=100,
        channel_id=200,
        channel_name="general",
        author_id=300 + message_id,
        author_display_name=f"user-{message_id}",
        content=raw_content,
        language=source_language,
        analysis_content=analysis_content,
        analysis_language="ko",
        analysis_content_source=content_source,
        source_content_hash=calculate_source_content_hash(raw_content),
        translation_id=translation_id,
        created_at=created_at,
    )


def make_dataset(messages: list[AnalysisMessageDTO]) -> AnalysisDatasetDTO:
    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[200],
        start_at=datetime(2026, 9, 8, tzinfo=UTC),
        end_at=datetime(2026, 9, 9, tzinfo=UTC),
    )
    return AnalysisDatasetDTO(
        scope=scope,
        messages=messages,
        metadata=AnalysisDatasetMetadataDTO(
            message_count=len(messages),
            author_count=len({message.author_id for message in messages}),
            channel_count=len({message.channel_id for message in messages}),
            language_distribution={"ko": 1.0} if messages else {},
        ),
    )


def make_request(
    *,
    output_language: str = "ko",
    max_messages: int = 100,
    max_total_characters: int = 10_000,
) -> AnalysisRunRequestDTO:
    return AnalysisRunRequestDTO(
        analysis_request=AnalysisRequestDTO(
            guild_id=100,
            start_at=datetime(2026, 9, 8, tzinfo=UTC),
            end_at=datetime(2026, 9, 9, tzinfo=UTC),
            output_language=output_language,
        ),
        limits=AnalysisRunLimitsDTO(
            max_messages=max_messages,
            max_total_characters=max_total_characters,
        ),
    )


def make_service(
    dataset: AnalysisDatasetDTO,
    detection_proposal: TopicDetectionProposalDTO,
    summary_proposal: TopicSummarizationProposalDTO,
):
    analysis = FakeAnalysisService(dataset)
    detector = FakeTopicDetectionProvider(detection_proposal)
    summarizer = FakeTopicSummarizationProvider(summary_proposal)
    service = AnalysisRunService(
        analysis,
        TopicDetectionService(detector),
        TopicSummarizationService(summarizer),
    )
    return service, analysis, detector, summarizer


def run(service: AnalysisRunService, request: AnalysisRunRequestDTO):
    async def execute():
        caller_thread_id = get_ident()
        result = await service.run(request)
        return result, caller_thread_id

    return asyncio.run(execute())


def test_composes_dataset_topics_and_summaries_with_provenance_off_thread():
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    translated = make_message(
        101,
        raw_content="game update",
        analysis_content="게임 업데이트",
        created_at=base_time,
        source_language="en",
        content_source=AnalysisTextSource.TRANSLATION,
        translation_id=501,
    )
    raw = make_message(
        102,
        raw_content="같이 플레이하자",
        analysis_content="같이 플레이하자",
        created_at=base_time + timedelta(minutes=1),
    )
    noise = make_message(
        103,
        raw_content="ㅋㅋ",
        analysis_content="ㅋㅋ",
        created_at=base_time + timedelta(minutes=2),
    )
    dataset = make_dataset([translated, raw, noise])
    service, analysis, detector, summarizer = make_service(
        dataset,
        TopicDetectionProposalDTO(
            topics=[TopicCandidateDTO(
                topic_id="game",
                label="게임 업데이트",
                message_ids=[101, 102],
            )],
            unassigned_message_ids=[103],
        ),
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="game",
                summary_text="업데이트 후 함께 플레이하기로 했다.",
                evidence_message_ids=[101, 102],
            )
        ]),
    )

    result, caller_thread_id = run(service, make_request())

    assert analysis.thread_id != caller_thread_id
    assert analysis.calls[0].output_language == "ko"
    assert [message.message_id for message in detector.calls[0]] == [101, 102, 103]
    assert detector.calls[0][0].analysis_content == "게임 업데이트"
    assert not hasattr(detector.calls[0][0], "content")
    assert summarizer.calls[0][0].output_language == "ko"

    assert result.scope == dataset.scope
    assert result.output_language == "ko"
    assert result.detector_id == "fake-topic-detector:v1"
    assert result.summarizer_id == "fake-topic-summarizer:v1"
    assert result.dataset_metadata == dataset.metadata
    assert result.input_message_count == 3
    assert result.input_analysis_character_count == sum(
        len(message.analysis_content)
        for message in dataset.messages
    )
    assert result.summaries[0].messages[0].source_content_hash == (
        translated.source_content_hash
    )
    assert result.summaries[0].messages[0].translation_id == 501
    assert result.summaries[0].evidence_message_ids == (101, 102)
    assert [message.message_id for message in result.unassigned_messages] == [103]


@pytest.mark.parametrize(
    ("max_messages", "max_total_characters", "error_match"),
    [
        (1, 10_000, "message count"),
        (100, 3, "character count"),
    ],
)
def test_limits_fail_before_provider_invocation(
    max_messages,
    max_total_characters,
    error_match,
):
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    dataset = make_dataset([
        make_message(
            201,
            raw_content="first",
            analysis_content="첫 번째",
            created_at=base_time,
        ),
        make_message(
            202,
            raw_content="second",
            analysis_content="두 번째",
            created_at=base_time + timedelta(minutes=1),
        ),
    ])
    service, analysis, detector, summarizer = make_service(
        dataset,
        TopicDetectionProposalDTO(topics=[], unassigned_message_ids=[]),
        TopicSummarizationProposalDTO(summaries=[]),
    )

    with pytest.raises(AnalysisRunLimitError, match=error_match):
        run(service, make_request(
            max_messages=max_messages,
            max_total_characters=max_total_characters,
        ))

    assert len(analysis.calls) == 1
    assert detector.calls == []
    assert summarizer.calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_messages", 0),
        ("max_total_characters", 0),
    ],
)
def test_limits_must_be_positive(field, value):
    values = {
        "max_messages": 10,
        "max_total_characters": 100,
    }
    values[field] = value

    with pytest.raises(ValidationError):
        AnalysisRunLimitsDTO(**values)


def test_empty_dataset_returns_empty_result_without_provider_calls():
    dataset = make_dataset([])
    service, analysis, detector, summarizer = make_service(
        dataset,
        TopicDetectionProposalDTO(topics=[], unassigned_message_ids=[]),
        TopicSummarizationProposalDTO(summaries=[]),
    )

    result, _ = run(service, make_request())

    assert len(analysis.calls) == 1
    assert detector.calls == []
    assert summarizer.calls == []
    assert result.input_message_count == 0
    assert result.input_analysis_character_count == 0
    assert result.summaries == ()
    assert result.unassigned_messages == ()


def test_detection_contract_failure_propagates_without_calling_summarizer():
    message = make_message(
        301,
        raw_content="source",
        analysis_content="분석",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    service, _, detector, summarizer = make_service(
        make_dataset([message]),
        TopicDetectionProposalDTO(
            topics=[TopicCandidateDTO(
                topic_id="invalid",
                message_ids=[999],
            )],
            unassigned_message_ids=[],
        ),
        TopicSummarizationProposalDTO(summaries=[]),
    )

    with pytest.raises(TopicDetectionContractError, match="outside"):
        run(service, make_request())

    assert len(detector.calls) == 1
    assert summarizer.calls == []


def test_summarization_contract_failure_propagates_without_output():
    message = make_message(
        401,
        raw_content="source",
        analysis_content="분석",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    service, _, detector, summarizer = make_service(
        make_dataset([message]),
        TopicDetectionProposalDTO(
            topics=[TopicCandidateDTO(
                topic_id="topic",
                message_ids=[401],
            )],
            unassigned_message_ids=[],
        ),
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="topic",
                summary_text="   ",
                evidence_message_ids=[401],
            )
        ]),
    )

    with pytest.raises(TopicSummarizationContractError, match="blank summary"):
        run(service, make_request())

    assert len(detector.calls) == 1
    assert len(summarizer.calls) == 1


def test_blank_output_language_fails_before_dataset_or_provider_calls():
    service, analysis, detector, summarizer = make_service(
        make_dataset([]),
        TopicDetectionProposalDTO(topics=[], unassigned_message_ids=[]),
        TopicSummarizationProposalDTO(summaries=[]),
    )

    with pytest.raises(AnalysisRunContractError, match="output_language"):
        run(service, make_request(output_language="   "))

    assert analysis.calls == []
    assert detector.calls == []
    assert summarizer.calls == []
