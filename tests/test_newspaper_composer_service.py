from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.dto.analysis_dataset_dto import AnalysisDatasetMetadataDTO
from app.dto.analysis_run_dto import AnalysisRunLimitsDTO, AnalysisRunResultDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.dto.analysis_text_dto import AnalysisTextSource
from app.dto.topic_detection_dto import TopicDetectionMessageDTO
from app.dto.topic_summarization_dto import TopicSummaryDTO
from app.services.newspaper_composer_service import (
    NewspaperCompositionError,
    NewspaperComposerService,
)


def make_message(
    message_id: int,
    *,
    analysis_content: str = "prepared text that must not be rendered",
    created_at: datetime | None = None,
    source_language: str = "ko",
    analysis_language: str = "ko",
    content_source: AnalysisTextSource = AnalysisTextSource.RAW,
    translation_id: int | None = None,
) -> TopicDetectionMessageDTO:
    return TopicDetectionMessageDTO(
        message_id=message_id,
        guild_id=100,
        channel_id=200 + message_id,
        channel_name=f"channel-{message_id}",
        author_id=300 + message_id,
        author_display_name=f"user-{message_id}",
        analysis_content=analysis_content,
        analysis_language=analysis_language,
        source_language=source_language,
        analysis_content_source=content_source,
        source_content_hash=f"hash-{message_id}",
        translation_id=translation_id,
        created_at=created_at or datetime(2026, 9, 8, tzinfo=UTC),
    )


def make_summary(
    topic_id: str,
    messages: tuple[TopicDetectionMessageDTO, ...],
    *,
    label: str | None = None,
    summary_text: str = "Validated topic summary",
    evidence_message_ids: tuple[int, ...] | None = None,
) -> TopicSummaryDTO:
    return TopicSummaryDTO(
        topic_id=topic_id,
        label=label,
        summary_text=summary_text,
        messages=messages,
        evidence_message_ids=(
            evidence_message_ids
            if evidence_message_ids is not None
            else tuple(message.message_id for message in messages)
        ),
    )


def make_run_result(
    *,
    summaries: tuple[TopicSummaryDTO, ...] = (),
    unassigned_messages: tuple[TopicDetectionMessageDTO, ...] = (),
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    output_language: str = "ko",
) -> AnalysisRunResultDTO:
    start_at = start_at or datetime(2026, 9, 8, tzinfo=UTC)
    end_at = end_at or start_at + timedelta(days=1)
    input_message_count = sum(
        len(summary.messages)
        for summary in summaries
    ) + len(unassigned_messages)
    return AnalysisRunResultDTO(
        scope=AnalysisScopeDTO(
            guild_id=100,
            channel_ids=[203, 201, 202],
            start_at=start_at,
            end_at=end_at,
        ),
        detector_id="fake-detector:v1",
        summarizer_id="fake-summarizer:v1",
        output_language=output_language,
        dataset_metadata=AnalysisDatasetMetadataDTO(
            message_count=input_message_count,
            author_count=input_message_count,
            channel_count=3 if input_message_count else 0,
            language_distribution={"ko": 1.0} if input_message_count else {},
        ),
        input_message_count=input_message_count,
        input_analysis_character_count=100,
        limits=AnalysisRunLimitsDTO(
            max_messages=100,
            max_total_characters=10_000,
        ),
        summaries=summaries,
        unassigned_messages=unassigned_messages,
    )


def test_composes_ordered_sections_with_evidence_and_content_free_provenance():
    base_time = datetime(2026, 9, 8, tzinfo=UTC)
    translated = make_message(
        101,
        analysis_content="translated prepared secret",
        created_at=base_time,
        source_language="en",
        content_source=AnalysisTextSource.TRANSLATION,
        translation_id=501,
    )
    raw = make_message(
        102,
        analysis_content="raw prepared secret",
        created_at=base_time + timedelta(minutes=1),
    )
    later = make_message(
        201,
        created_at=base_time + timedelta(hours=1),
    )
    noise = make_message(
        301,
        analysis_content="unassigned prepared secret",
        created_at=base_time + timedelta(hours=2),
    )
    analysis_run = make_run_result(
        summaries=(
            make_summary(
                "later-topic",
                (later,),
                label="Later topic",
                summary_text="Later validated summary",
            ),
            make_summary(
                "early-topic",
                (raw, translated),
                label="Early topic",
                summary_text="Early validated summary",
                evidence_message_ids=(101,),
            ),
        ),
        unassigned_messages=(noise,),
    )

    result = NewspaperComposerService().compose(analysis_run)

    assert [section.topic_id for section in result.sections] == [
        "early-topic",
        "later-topic",
    ]
    first = result.sections[0]
    assert first.section_number == 1
    assert first.topic_message_count == 2
    assert first.evidence_message_ids == (101,)
    assert first.evidence_message_count == 1
    assert [message.message_id for message in first.source_messages] == [101, 102]
    assert first.source_messages[0].analysis_content_source is (
        AnalysisTextSource.TRANSLATION
    )
    assert first.source_messages[0].translation_id == 501
    assert first.source_messages[1].analysis_content_source is AnalysisTextSource.RAW
    assert first.source_messages[1].translation_id is None
    assert result.unassigned_messages[0].message_id == 301
    assert "translated prepared secret" not in result.markdown_text
    assert "raw prepared secret" not in result.markdown_text
    assert "unassigned prepared secret" not in result.markdown_text
    for section in result.sections:
        for source_message in section.source_messages:
            assert not hasattr(source_message, "analysis_content")
    for source_message in result.unassigned_messages:
        assert not hasattr(source_message, "analysis_content")


def test_identical_validated_input_produces_byte_identical_markdown():
    created_at = datetime(2026, 9, 8, tzinfo=UTC)
    first = make_message(11, created_at=created_at)
    second = make_message(12, created_at=created_at)
    analysis_run = make_run_result(
        summaries=(
            make_summary("second-topic", (second,)),
            make_summary("first-topic", (first,)),
        ),
    )
    composer = NewspaperComposerService()

    first_result = composer.compose(analysis_run)
    first_markdown = first_result.markdown_text.encode("utf-8")
    second_markdown = composer.compose(analysis_run).markdown_text.encode("utf-8")

    assert [section.topic_id for section in first_result.sections] == [
        "first-topic",
        "second-topic",
    ]
    assert first_markdown == second_markdown


def test_missing_label_uses_a_structural_topic_heading_only():
    message = make_message(21)
    result = NewspaperComposerService().compose(make_run_result(
        summaries=(make_summary(
            "unlabeled-topic",
            (message,),
            label=None,
            summary_text="Supported summary",
        ),),
    ))

    assert result.sections[0].label is None
    assert "### Topic 1\n" in result.markdown_text
    assert "### Topic 1:" not in result.markdown_text
    assert r"- Topic ID: unlabeled\-topic" in result.markdown_text


def test_hostile_markdown_text_cannot_create_edition_structure():
    message = make_message(31)
    result = NewspaperComposerService().compose(make_run_result(
        summaries=(make_summary(
            "topic](bad)",
            (message,),
            label="# Fake heading\n[link](https://example.invalid) | cell",
            summary_text=(
                "<script>alert('x')</script>\n"
                "## Injected heading\n- fake item"
            ),
        ),),
        output_language="ko | injected",
    ))

    headings = [
        line
        for line in result.markdown_text.splitlines()
        if line.startswith("#")
    ]
    assert headings == [
        "# Project Chronicle Newspaper",
        "## Edition",
        "## Topics",
        "### Topic 1: \\# Fake heading<br>",
        "#### Summary",
        "#### Source provenance",
        "## Unassigned / Noise",
    ]
    assert "<script>" not in result.markdown_text
    assert "&lt;script&gt;" in result.markdown_text
    assert "\\#\\# Injected heading" in result.markdown_text
    assert "\\[link\\]\\(https://example\\.invalid\\) \\| cell" in (
        result.markdown_text
    )


def test_zero_topics_keeps_unassigned_noise_explicit_without_a_section():
    later_noise = make_message(
        42,
        created_at=datetime(2026, 9, 8, 2, tzinfo=UTC),
    )
    earlier_noise = make_message(
        41,
        created_at=datetime(2026, 9, 8, 1, tzinfo=UTC),
    )

    result = NewspaperComposerService().compose(make_run_result(
        unassigned_messages=(later_noise, earlier_noise),
    ))

    assert result.sections == ()
    assert result.edition.topic_count == 0
    assert result.edition.unassigned_message_count == 2
    assert [message.message_id for message in result.unassigned_messages] == [41, 42]
    assert "No topic sections were produced." in result.markdown_text
    assert "- Unassigned/noise messages: 2" in result.markdown_text
    assert "### Topic" not in result.markdown_text


def test_edition_date_and_display_period_are_derived_in_kst():
    start_at = datetime(2026, 9, 8, 16, 30, tzinfo=UTC)
    end_at = datetime(2026, 9, 9, 16, 30, tzinfo=UTC)

    result = NewspaperComposerService().compose(make_run_result(
        start_at=start_at,
        end_at=end_at,
    ))

    assert result.edition.edition_date.isoformat() == "2026-09-09"
    assert result.edition.display_timezone == "Asia/Seoul"
    assert result.edition.scope_start_at_utc == start_at
    assert result.edition.scope_start_at_kst.utcoffset() == timedelta(hours=9)
    assert "- Edition date \\(KST\\): 2026-09-09" in result.markdown_text
    assert "- Scope start \\(KST\\): 2026-09-09 01:30:00 KST" in (
        result.markdown_text
    )
    assert "- Scope end, exclusive \\(KST\\): 2026-09-10 01:30:00 KST" in (
        result.markdown_text
    )


def test_result_contract_is_immutable_and_has_deterministic_channel_order():
    result = NewspaperComposerService().compose(make_run_result())

    assert result.edition.channel_ids == (201, 202, 203)
    with pytest.raises(ValidationError):
        result.output_language = "en"
    with pytest.raises(ValidationError):
        result.edition.topic_count = 10


def test_rejects_values_outside_the_analysis_run_result_boundary():
    with pytest.raises(
        NewspaperCompositionError,
        match="must be an AnalysisRunResultDTO",
    ):
        NewspaperComposerService().compose(object())
