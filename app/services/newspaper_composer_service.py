import html
import re
from datetime import datetime

from app.dto.analysis_run_dto import AnalysisRunResultDTO
from app.dto.newspaper_dto import (
    NewspaperEditionMetadataDTO,
    NewspaperMessageProvenanceDTO,
    NewspaperResultDTO,
    NewspaperSectionDTO,
)
from app.dto.topic_detection_dto import TopicDetectionMessageDTO
from app.dto.topic_summarization_dto import TopicSummaryDTO
from app.utils.datetime_utils import ensure_utc, to_kst


class NewspaperCompositionError(ValueError):
    """Raised when a value is not a valid completed analysis-run result."""


class NewspaperComposerService:
    """Compose validated analysis results into deterministic Markdown."""

    _markdown_specials = re.compile(r"([\\`*_{}\[\]()#+.!|>~\-])")

    def compose(self, analysis_run: AnalysisRunResultDTO) -> NewspaperResultDTO:
        self._validate_analysis_run(analysis_run)

        ordered_summaries = sorted(
            analysis_run.summaries,
            key=self._section_order,
        )
        sections = tuple(
            self._build_section(section_number, summary)
            for section_number, summary in enumerate(
                ordered_summaries,
                start=1,
            )
        )
        unassigned_messages = tuple(
            self._to_provenance(message)
            for message in sorted(
                analysis_run.unassigned_messages,
                key=self._message_order,
            )
        )

        scope_start_at_utc = ensure_utc(analysis_run.scope.start_at)
        scope_end_at_utc = ensure_utc(analysis_run.scope.end_at)
        scope_start_at_kst = to_kst(scope_start_at_utc)
        scope_end_at_kst = to_kst(scope_end_at_utc)
        edition = NewspaperEditionMetadataDTO(
            edition_date=scope_start_at_kst.date(),
            display_timezone="Asia/Seoul",
            guild_id=analysis_run.scope.guild_id,
            channel_ids=tuple(sorted(analysis_run.scope.channel_ids)),
            scope_start_at_utc=scope_start_at_utc,
            scope_end_at_utc=scope_end_at_utc,
            scope_start_at_kst=scope_start_at_kst,
            scope_end_at_kst=scope_end_at_kst,
            input_message_count=analysis_run.input_message_count,
            topic_count=len(sections),
            unassigned_message_count=len(unassigned_messages),
        )
        markdown_text = self._render_markdown(
            edition=edition,
            output_language=analysis_run.output_language,
            detector_id=analysis_run.detector_id,
            summarizer_id=analysis_run.summarizer_id,
            sections=sections,
            unassigned_messages=unassigned_messages,
        )

        return NewspaperResultDTO(
            edition=edition,
            output_language=analysis_run.output_language,
            detector_id=analysis_run.detector_id,
            summarizer_id=analysis_run.summarizer_id,
            sections=sections,
            unassigned_messages=unassigned_messages,
            markdown_text=markdown_text,
        )

    @staticmethod
    def _validate_analysis_run(analysis_run: AnalysisRunResultDTO) -> None:
        if not isinstance(analysis_run, AnalysisRunResultDTO):
            raise NewspaperCompositionError(
                "newspaper input must be an AnalysisRunResultDTO"
            )
        if analysis_run.scope.start_at >= analysis_run.scope.end_at:
            raise NewspaperCompositionError(
                "analysis scope start_at must be earlier than end_at"
            )

    @classmethod
    def _section_order(cls, summary: TopicSummaryDTO) -> tuple:
        if not summary.messages:
            raise NewspaperCompositionError(
                f"topic {summary.topic_id} contains no source messages"
            )
        first_message = min(summary.messages, key=cls._message_order)
        return (
            first_message.created_at,
            first_message.message_id,
            summary.topic_id,
        )

    @classmethod
    def _build_section(
        cls,
        section_number: int,
        summary: TopicSummaryDTO,
    ) -> NewspaperSectionDTO:
        messages = tuple(sorted(summary.messages, key=cls._message_order))
        label = (
            summary.label.strip()
            if summary.label and summary.label.strip()
            else None
        )

        return NewspaperSectionDTO(
            section_number=section_number,
            topic_id=summary.topic_id,
            label=label,
            summary_text=summary.summary_text,
            topic_message_count=len(messages),
            evidence_message_ids=summary.evidence_message_ids,
            evidence_message_count=len(summary.evidence_message_ids),
            source_messages=tuple(
                cls._to_provenance(message)
                for message in messages
            ),
        )

    @staticmethod
    def _to_provenance(
        message: TopicDetectionMessageDTO,
    ) -> NewspaperMessageProvenanceDTO:
        return NewspaperMessageProvenanceDTO(
            message_id=message.message_id,
            channel_id=message.channel_id,
            created_at_utc=ensure_utc(message.created_at),
            source_language=message.source_language,
            analysis_language=message.analysis_language,
            analysis_content_source=message.analysis_content_source,
            source_content_hash=message.source_content_hash,
            translation_id=message.translation_id,
        )

    @staticmethod
    def _message_order(message: TopicDetectionMessageDTO) -> tuple:
        return (message.created_at, message.message_id)

    @classmethod
    def _escape_markdown(cls, value: str) -> str:
        escaped_html = html.escape(value, quote=False)
        escaped_lines = (
            cls._markdown_specials.sub(r"\\\1", line)
            for line in escaped_html.replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )
        return "<br>\n".join(escaped_lines)

    @staticmethod
    def _format_kst(value: datetime) -> str:
        return to_kst(value).strftime("%Y-%m-%d %H:%M:%S KST")

    @classmethod
    def _render_provenance(
        cls,
        message: NewspaperMessageProvenanceDTO,
    ) -> str:
        translation_id = (
            str(message.translation_id)
            if message.translation_id is not None
            else "none"
        )
        return (
            f"  - Message {message.message_id} | "
            f"created at \\(KST\\): {cls._format_kst(message.created_at_utc)} | "
            f"channel ID: {message.channel_id} | "
            "source hash: "
            f"{cls._escape_markdown(message.source_content_hash)} | "
            "analysis source: "
            f"{cls._escape_markdown(message.analysis_content_source.value)} | "
            "source language: "
            f"{cls._escape_markdown(message.source_language)} | "
            "analysis language: "
            f"{cls._escape_markdown(message.analysis_language)} | "
            f"translation ID: {translation_id}"
        )

    @classmethod
    def _render_markdown(
        cls,
        *,
        edition: NewspaperEditionMetadataDTO,
        output_language: str,
        detector_id: str,
        summarizer_id: str,
        sections: tuple[NewspaperSectionDTO, ...],
        unassigned_messages: tuple[NewspaperMessageProvenanceDTO, ...],
    ) -> str:
        channel_ids = ", ".join(str(value) for value in edition.channel_ids)
        lines = [
            "# Project Chronicle Newspaper",
            "",
            "## Edition",
            "",
            f"- Edition date \\(KST\\): {edition.edition_date.isoformat()}",
            "- Scope start \\(KST\\): "
            f"{cls._format_kst(edition.scope_start_at_kst)}",
            "- Scope end, exclusive \\(KST\\): "
            f"{cls._format_kst(edition.scope_end_at_kst)}",
            f"- Guild ID: {edition.guild_id}",
            f"- Channel IDs: {channel_ids or 'none'}",
            "- Output language: "
            f"{cls._escape_markdown(output_language)}",
            f"- Detector: {cls._escape_markdown(detector_id)}",
            f"- Summarizer: {cls._escape_markdown(summarizer_id)}",
            f"- Input messages: {edition.input_message_count}",
            f"- Topic sections: {edition.topic_count}",
            "- Unassigned/noise messages: "
            f"{edition.unassigned_message_count}",
            "",
            "## Topics",
            "",
        ]

        if not sections:
            lines.extend(["No topic sections were produced.", ""])
        else:
            for section in sections:
                heading = f"### Topic {section.section_number}"
                if section.label is not None:
                    heading += f": {cls._escape_markdown(section.label)}"
                evidence_ids = ", ".join(
                    str(message_id)
                    for message_id in section.evidence_message_ids
                )
                lines.extend([
                    heading,
                    "",
                    f"- Topic ID: {cls._escape_markdown(section.topic_id)}",
                    f"- Topic messages: {section.topic_message_count}",
                    "- Evidence messages "
                    f"\\({section.evidence_message_count}\\): {evidence_ids}",
                    "",
                    "#### Summary",
                    "",
                    cls._escape_markdown(section.summary_text),
                    "",
                    "#### Source provenance",
                    "",
                ])
                lines.extend(
                    cls._render_provenance(message)
                    for message in section.source_messages
                )
                lines.append("")

        lines.extend([
            "## Unassigned / Noise",
            "",
            f"- Message count: {edition.unassigned_message_count}",
        ])
        if unassigned_messages:
            lines.extend(["- Source provenance:"])
            lines.extend(
                cls._render_provenance(message)
                for message in unassigned_messages
            )
        else:
            lines.append("- Source provenance: none")

        return "\n".join(lines) + "\n"
