import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from app.dto.analysis_dataset_dto import (
    AnalysisDatasetDTO,
    AnalysisDatasetMetadataDTO,
)
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.dto.topic_detection_dto import (
    TopicCandidateDTO,
    TopicDetectionProposalDTO,
)
from app.services.topic_detection_service import (
    TopicDetectionContractError,
    TopicDetectionService,
)
from app.utils.content_hash import calculate_source_content_hash


class FakeTopicDetectionProvider:
    detector_id = "fake-topic-detector:v1"

    def __init__(self, proposal: TopicDetectionProposalDTO):
        self.proposal = proposal
        self.calls = []

    async def detect_topics(self, messages):
        self.calls.append(messages)
        return self.proposal


def make_message(
    message_id: int,
    *,
    raw_content: str,
    source_language: str,
    analysis_content: str | None = None,
    analysis_language: str | None = None,
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
        analysis_content=analysis_content or raw_content,
        analysis_language=analysis_language or source_language,
        analysis_content_source=content_source,
        source_content_hash=calculate_source_content_hash(raw_content),
        translation_id=translation_id,
        created_at=datetime(2026, 9, 8, tzinfo=UTC)
        + timedelta(minutes=message_id),
    )


def make_dataset(messages: list[AnalysisMessageDTO]) -> AnalysisDatasetDTO:
    return AnalysisDatasetDTO(
        scope=AnalysisScopeDTO(
            guild_id=100,
            channel_ids=[200],
            start_at=datetime(2026, 9, 8, tzinfo=UTC),
            end_at=datetime(2026, 9, 9, tzinfo=UTC),
        ),
        messages=messages,
        metadata=AnalysisDatasetMetadataDTO(
            message_count=len(messages),
            author_count=len({message.author_id for message in messages}),
            channel_count=len({message.channel_id for message in messages}),
            language_distribution={},
        ),
    )


def detect(service: TopicDetectionService, dataset: AnalysisDatasetDTO):
    return asyncio.run(service.detect_topics(dataset))


def test_groups_multiple_messages_and_uses_prepared_analysis_content():
    messages = [
        make_message(
            101,
            raw_content="game update",
            source_language="en",
            analysis_content="게임 업데이트",
            analysis_language="ko",
            content_source=AnalysisTextSource.TRANSLATION,
            translation_id=501,
        ),
        make_message(
            102,
            raw_content="같이 플레이하자",
            source_language="ko",
        ),
        make_message(
            103,
            raw_content="서버 점검",
            source_language="ko",
        ),
    ]
    provider = FakeTopicDetectionProvider(TopicDetectionProposalDTO(
        topics=[
            TopicCandidateDTO(
                topic_id="game-update",
                label="게임 업데이트",
                message_ids=[101, 102],
            ),
            TopicCandidateDTO(
                topic_id="server-maintenance",
                label="서버 점검",
                message_ids=[103],
            ),
        ],
        unassigned_message_ids=[],
    ))

    result = detect(TopicDetectionService(provider), make_dataset(messages))

    provider_inputs = provider.calls[0]
    assert provider_inputs[0].analysis_content == "게임 업데이트"
    assert not hasattr(provider_inputs[0], "content")
    assert [topic.topic_id for topic in result.topics] == [
        "game-update",
        "server-maintenance",
    ]
    assert [
        membership.message.message_id
        for membership in result.topics[0].memberships
    ] == [101, 102]
    assert messages[0].content == "game update"


def test_preserves_mixed_languages_translation_provenance_and_noise():
    messages = [
        make_message(
            201,
            raw_content="hello",
            source_language="en",
            analysis_content="안녕하세요",
            analysis_language="ko",
            content_source=AnalysisTextSource.TRANSLATION,
            translation_id=601,
        ),
        make_message(
            202,
            raw_content="こんにちは",
            source_language="ja",
        ),
        make_message(
            203,
            raw_content="lol",
            source_language="en",
        ),
    ]
    provider = FakeTopicDetectionProvider(TopicDetectionProposalDTO(
        topics=[TopicCandidateDTO(
            topic_id="greetings",
            label="인사",
            message_ids=[201, 202],
        )],
        unassigned_message_ids=[203],
    ))

    result = detect(TopicDetectionService(provider), make_dataset(messages))
    members = [
        membership.message
        for membership in result.topics[0].memberships
    ]

    assert [(member.source_language, member.analysis_language) for member in members] == [
        ("en", "ko"),
        ("ja", "ja"),
    ]
    assert members[0].analysis_content_source is AnalysisTextSource.TRANSLATION
    assert members[0].translation_id == 601
    assert members[1].analysis_content_source is AnalysisTextSource.RAW
    assert members[1].translation_id is None
    assert [message.message_id for message in result.unassigned_messages] == [203]
    assert result.unassigned_messages[0].analysis_content == "lol"


def test_empty_dataset_returns_empty_result_without_calling_provider():
    provider = FakeTopicDetectionProvider(TopicDetectionProposalDTO(
        topics=[],
        unassigned_message_ids=[],
    ))

    result = detect(TopicDetectionService(provider), make_dataset([]))

    assert result.topics == []
    assert result.unassigned_messages == []
    assert provider.calls == []


def test_provider_cannot_reintroduce_deleted_message_outside_dataset():
    dataset = make_dataset([
        make_message(301, raw_content="active", source_language="ko"),
    ])
    provider = FakeTopicDetectionProvider(TopicDetectionProposalDTO(
        topics=[TopicCandidateDTO(
            topic_id="invalid",
            message_ids=[301, 999],
        )],
        unassigned_message_ids=[],
    ))

    with pytest.raises(TopicDetectionContractError, match="outside"):
        detect(TopicDetectionService(provider), dataset)


def test_provider_must_explicitly_assign_or_mark_every_message_unassigned():
    dataset = make_dataset([
        make_message(401, raw_content="first", source_language="en"),
        make_message(402, raw_content="second", source_language="en"),
    ])
    provider = FakeTopicDetectionProvider(TopicDetectionProposalDTO(
        topics=[TopicCandidateDTO(topic_id="partial", message_ids=[401])],
        unassigned_message_ids=[],
    ))

    with pytest.raises(TopicDetectionContractError, match="omitted"):
        detect(TopicDetectionService(provider), dataset)


def test_provider_topic_and_message_identity_remain_stable():
    dataset = make_dataset([
        make_message(501, raw_content="one", source_language="en"),
        make_message(502, raw_content="two", source_language="en"),
    ])
    proposal = TopicDetectionProposalDTO(
        topics=[TopicCandidateDTO(
            topic_id="stable-topic-id",
            message_ids=[502, 501],
        )],
        unassigned_message_ids=[],
    )
    provider = FakeTopicDetectionProvider(proposal)
    service = TopicDetectionService(provider)

    first = detect(service, dataset)
    second = detect(service, dataset)

    assert first == second
    assert first.topics[0].topic_id == "stable-topic-id"
    assert [
        membership.message.message_id
        for membership in first.topics[0].memberships
    ] == [502, 501]
