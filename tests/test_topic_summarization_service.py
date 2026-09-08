import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.dto.topic_detection_dto import (
    DetectedTopicDTO,
    TopicDetectionMessageDTO,
    TopicDetectionResultDTO,
    TopicMembershipDTO,
)
from app.dto.topic_summarization_dto import (
    TopicSummarizationProposalDTO,
    TopicSummaryCandidateDTO,
)
from app.services.topic_summarization_service import (
    TopicSummarizationContractError,
    TopicSummarizationService,
)
from app.utils.content_hash import calculate_source_content_hash


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
    content: str,
    created_at: datetime,
    source_language: str = "ko",
    content_source: AnalysisTextSource = AnalysisTextSource.RAW,
    translation_id: int | None = None,
) -> TopicDetectionMessageDTO:
    return TopicDetectionMessageDTO(
        message_id=message_id,
        guild_id=100,
        channel_id=200,
        channel_name="general",
        author_id=300 + message_id,
        author_display_name=f"user-{message_id}",
        analysis_content=content,
        analysis_language="ko",
        source_language=source_language,
        analysis_content_source=content_source,
        source_content_hash=calculate_source_content_hash(
            f"raw-source-{message_id}"
        ),
        translation_id=translation_id,
        created_at=created_at,
    )


def make_topic(
    topic_id: str,
    messages: list[TopicDetectionMessageDTO],
    label: str | None = None,
) -> DetectedTopicDTO:
    return DetectedTopicDTO(
        topic_id=topic_id,
        label=label,
        memberships=[
            TopicMembershipDTO(topic_id=topic_id, message=message)
            for message in messages
        ],
    )


def make_result(
    topics: list[DetectedTopicDTO],
    unassigned_messages: list[TopicDetectionMessageDTO] | None = None,
) -> TopicDetectionResultDTO:
    return TopicDetectionResultDTO(
        scope=AnalysisScopeDTO(
            guild_id=100,
            channel_ids=[200],
            start_at=datetime(2026, 9, 8, tzinfo=UTC),
            end_at=datetime(2026, 9, 9, tzinfo=UTC),
        ),
        detector_id="fake-topic-detector:v1",
        topics=topics,
        unassigned_messages=unassigned_messages or [],
    )


def summarize(
    provider: FakeTopicSummarizationProvider,
    detected: TopicDetectionResultDTO,
    output_language: str = "ko",
):
    return asyncio.run(
        TopicSummarizationService(provider).summarize_topics(
            detected,
            output_language,
        )
    )


def test_summarizes_topics_with_prepared_content_and_full_provenance():
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    translated = make_message(
        101,
        content="번역된 업데이트 소식",
        created_at=base_time,
        source_language="en",
        content_source=AnalysisTextSource.TRANSLATION,
        translation_id=501,
    )
    raw = make_message(
        102,
        content="같이 플레이하자",
        created_at=base_time + timedelta(minutes=1),
    )
    noise = make_message(
        103,
        content="ㅋㅋ",
        created_at=base_time + timedelta(minutes=2),
    )
    detected = make_result(
        [make_topic("game-update", [translated, raw], "게임 업데이트")],
        [noise],
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="game-update",
                summary_text="업데이트 이후 함께 플레이하기로 했다.",
                evidence_message_ids=[101, 102],
            )
        ])
    )

    result = summarize(provider, detected)

    provider_topic = provider.calls[0][0]
    assert provider_topic.output_language == "ko"
    assert provider_topic.label == "게임 업데이트"
    assert provider_topic.messages[0].analysis_content == "번역된 업데이트 소식"
    assert not hasattr(provider_topic.messages[0], "content")
    assert provider_topic.messages[0].source_content_hash == (
        translated.source_content_hash
    )
    assert provider_topic.messages[0].translation_id == 501

    summary = result.summaries[0]
    assert summary.topic_id == "game-update"
    assert summary.summary_text == "업데이트 이후 함께 플레이하기로 했다."
    assert summary.messages == (translated, raw)
    assert summary.evidence_message_ids == (101, 102)
    assert result.scope == detected.scope
    assert result.detector_id == "fake-topic-detector:v1"
    assert result.summarizer_id == "fake-topic-summarizer:v1"
    assert result.output_language == "ko"
    assert result.unassigned_messages == (noise,)


def test_provider_messages_and_evidence_are_ordered_deterministically():
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    later = make_message(
        203,
        content="later",
        created_at=base_time + timedelta(minutes=1),
    )
    same_time_high_id = make_message(
        202,
        content="same time high ID",
        created_at=base_time,
    )
    same_time_low_id = make_message(
        201,
        content="same time low ID",
        created_at=base_time,
    )
    detected = make_result([
        make_topic(
            "ordered",
            [later, same_time_high_id, same_time_low_id],
        )
    ])
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="ordered",
                summary_text="ordered summary",
                evidence_message_ids=[203, 202, 201],
            )
        ])
    )

    result = summarize(provider, detected)

    provider_ids = [
        message.message_id
        for message in provider.calls[0][0].messages
    ]
    assert provider_ids == [201, 202, 203]
    assert result.summaries[0].evidence_message_ids == (201, 202, 203)


def test_provider_input_and_materialized_result_are_immutable():
    message = make_message(
        301,
        content="immutable",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="immutable-topic",
                summary_text="immutable summary",
                evidence_message_ids=[301],
            )
        ])
    )

    result = summarize(
        provider,
        make_result([make_topic("immutable-topic", [message])]),
    )

    with pytest.raises(ValidationError):
        provider.calls[0][0].output_language = "en"
    with pytest.raises(ValidationError):
        result.summaries[0].summary_text = "changed"


def test_empty_topic_result_does_not_call_provider_and_preserves_noise():
    noise = make_message(
        401,
        content="noise",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[])
    )

    result = summarize(provider, make_result([], [noise]))

    assert result.summaries == ()
    assert result.unassigned_messages == (noise,)
    assert provider.calls == []


def test_rejects_duplicate_topic_summaries():
    message = make_message(
        501,
        content="topic",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    duplicate = TopicSummaryCandidateDTO(
        topic_id="duplicate",
        summary_text="summary",
        evidence_message_ids=[501],
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[duplicate, duplicate])
    )

    with pytest.raises(TopicSummarizationContractError, match="duplicate topic"):
        summarize(provider, make_result([make_topic("duplicate", [message])]))


def test_rejects_unknown_topic_summary():
    message = make_message(
        601,
        content="topic",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="unknown",
                summary_text="summary",
                evidence_message_ids=[601],
            )
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="unknown topic"):
        summarize(provider, make_result([make_topic("known", [message])]))


def test_rejects_omitted_topic_summary():
    first = make_message(
        701,
        content="first",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    second = make_message(
        702,
        content="second",
        created_at=datetime(2026, 9, 8, 1, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="first",
                summary_text="summary",
                evidence_message_ids=[701],
            )
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="omitted"):
        summarize(
            provider,
            make_result([
                make_topic("first", [first]),
                make_topic("second", [second]),
            ]),
        )


@pytest.mark.parametrize("summary_text", ["", "   "])
def test_rejects_blank_summary(summary_text):
    message = make_message(
        801,
        content="topic",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="blank",
                summary_text=summary_text,
                evidence_message_ids=[801],
            )
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="blank summary"):
        summarize(provider, make_result([make_topic("blank", [message])]))


def test_rejects_empty_evidence():
    message = make_message(
        901,
        content="topic",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="no-evidence",
                summary_text="summary",
                evidence_message_ids=[],
            )
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="no evidence"):
        summarize(
            provider,
            make_result([make_topic("no-evidence", [message])]),
        )


def test_rejects_duplicate_evidence_ids():
    message = make_message(
        1001,
        content="topic",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="duplicate-evidence",
                summary_text="summary",
                evidence_message_ids=[1001, 1001],
            )
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="duplicate evidence"):
        summarize(
            provider,
            make_result([make_topic("duplicate-evidence", [message])]),
        )


def test_rejects_evidence_outside_its_topic():
    first = make_message(
        1101,
        content="first",
        created_at=datetime(2026, 9, 8, tzinfo=UTC),
    )
    second = make_message(
        1102,
        content="second",
        created_at=datetime(2026, 9, 8, 1, tzinfo=UTC),
    )
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[
            TopicSummaryCandidateDTO(
                topic_id="first",
                summary_text="first summary",
                evidence_message_ids=[1102],
            ),
            TopicSummaryCandidateDTO(
                topic_id="second",
                summary_text="second summary",
                evidence_message_ids=[1102],
            ),
        ])
    )

    with pytest.raises(TopicSummarizationContractError, match="outside topic first"):
        summarize(
            provider,
            make_result([
                make_topic("first", [first]),
                make_topic("second", [second]),
            ]),
        )


@pytest.mark.parametrize("summarizer_id", ["", "   "])
def test_rejects_blank_summarizer_id(summarizer_id):
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[])
    )
    provider.summarizer_id = summarizer_id

    with pytest.raises(TopicSummarizationContractError, match="summarizer_id"):
        summarize(provider, make_result([]))


@pytest.mark.parametrize("output_language", ["", "   "])
def test_rejects_blank_output_language(output_language):
    provider = FakeTopicSummarizationProvider(
        TopicSummarizationProposalDTO(summaries=[])
    )

    with pytest.raises(TopicSummarizationContractError, match="output_language"):
        summarize(provider, make_result([]), output_language)
