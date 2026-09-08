from app.dto.topic_detection_dto import (
    DetectedTopicDTO,
    TopicDetectionMessageDTO,
    TopicDetectionResultDTO,
)
from app.dto.topic_summarization_dto import (
    TopicSummarizationInputDTO,
    TopicSummarizationResultDTO,
    TopicSummaryDTO,
)
from app.services.topic_summarization_provider import TopicSummarizationProvider


class TopicSummarizationContractError(ValueError):
    """Raised when summary input or provider output violates identity contracts."""


class TopicSummarizationService:
    """Prepare topic inputs and validate evidence-linked provider summaries."""

    def __init__(self, provider: TopicSummarizationProvider):
        self.provider = provider

    async def summarize_topics(
        self,
        detected: TopicDetectionResultDTO,
        output_language: str,
    ) -> TopicSummarizationResultDTO:
        summarizer_id = self._required_text(
            self.provider.summarizer_id,
            "summarizer_id",
        )
        output_language = self._required_text(
            output_language,
            "output_language",
        )

        topic_ids = [topic.topic_id for topic in detected.topics]
        if len(topic_ids) != len(set(topic_ids)):
            raise TopicSummarizationContractError(
                "topic detection result contains duplicate topic IDs"
            )

        prepared_topics = tuple(
            self._to_provider_input(topic, output_language)
            for topic in detected.topics
        )
        unassigned_messages = tuple(sorted(
            detected.unassigned_messages,
            key=self._message_order,
        ))

        if not prepared_topics:
            return TopicSummarizationResultDTO(
                scope=detected.scope,
                detector_id=detected.detector_id,
                summarizer_id=summarizer_id,
                output_language=output_language,
                summaries=(),
                unassigned_messages=unassigned_messages,
            )

        proposal = await self.provider.summarize_topics(prepared_topics)
        proposed_topic_ids = [
            summary.topic_id
            for summary in proposal.summaries
        ]
        if len(proposed_topic_ids) != len(set(proposed_topic_ids)):
            raise TopicSummarizationContractError(
                "provider returned duplicate topic summaries"
            )

        known_topic_ids = set(topic_ids)
        proposed_topic_id_set = set(proposed_topic_ids)
        unknown_topic_ids = proposed_topic_id_set - known_topic_ids
        if unknown_topic_ids:
            raise TopicSummarizationContractError(
                "provider returned summaries for unknown topic IDs: "
                + ", ".join(sorted(unknown_topic_ids))
            )

        missing_topic_ids = known_topic_ids - proposed_topic_id_set
        if missing_topic_ids:
            raise TopicSummarizationContractError(
                "provider omitted detected topic IDs: "
                + ", ".join(sorted(missing_topic_ids))
            )

        proposals_by_topic_id = {
            summary.topic_id: summary
            for summary in proposal.summaries
        }
        prepared_by_topic_id = {
            topic.topic_id: topic
            for topic in prepared_topics
        }
        summaries = []

        for detected_topic in detected.topics:
            candidate = proposals_by_topic_id[detected_topic.topic_id]
            prepared_topic = prepared_by_topic_id[detected_topic.topic_id]
            summary_text = candidate.summary_text.strip()
            if not summary_text:
                raise TopicSummarizationContractError(
                    "provider returned a blank summary for topic "
                    f"{detected_topic.topic_id}"
                )

            evidence_ids = candidate.evidence_message_ids
            if not evidence_ids:
                raise TopicSummarizationContractError(
                    "provider returned no evidence for topic "
                    f"{detected_topic.topic_id}"
                )
            if len(evidence_ids) != len(set(evidence_ids)):
                raise TopicSummarizationContractError(
                    "provider returned duplicate evidence message IDs for topic "
                    f"{detected_topic.topic_id}"
                )

            member_ids = {
                message.message_id
                for message in prepared_topic.messages
            }
            invalid_evidence_ids = set(evidence_ids) - member_ids
            if invalid_evidence_ids:
                raise TopicSummarizationContractError(
                    "provider returned evidence outside topic "
                    f"{detected_topic.topic_id}: "
                    + ", ".join(
                        str(message_id)
                        for message_id in sorted(invalid_evidence_ids)
                    )
                )

            evidence_id_set = set(evidence_ids)
            ordered_evidence_ids = tuple(
                message.message_id
                for message in prepared_topic.messages
                if message.message_id in evidence_id_set
            )
            summaries.append(TopicSummaryDTO(
                topic_id=detected_topic.topic_id,
                label=detected_topic.label,
                summary_text=summary_text,
                messages=prepared_topic.messages,
                evidence_message_ids=ordered_evidence_ids,
            ))

        return TopicSummarizationResultDTO(
            scope=detected.scope,
            detector_id=detected.detector_id,
            summarizer_id=summarizer_id,
            output_language=output_language,
            summaries=tuple(summaries),
            unassigned_messages=unassigned_messages,
        )

    @classmethod
    def _to_provider_input(
        cls,
        topic: DetectedTopicDTO,
        output_language: str,
    ) -> TopicSummarizationInputDTO:
        messages = tuple(sorted(
            (membership.message for membership in topic.memberships),
            key=cls._message_order,
        ))
        if not messages:
            raise TopicSummarizationContractError(
                f"detected topic {topic.topic_id} contains no messages"
            )

        message_ids = [message.message_id for message in messages]
        if len(message_ids) != len(set(message_ids)):
            raise TopicSummarizationContractError(
                f"detected topic {topic.topic_id} contains duplicate messages"
            )

        return TopicSummarizationInputDTO(
            topic_id=topic.topic_id,
            label=topic.label,
            messages=messages,
            output_language=output_language,
        )

    @staticmethod
    def _message_order(
        message: TopicDetectionMessageDTO,
    ) -> tuple:
        return (message.created_at, message.message_id)

    @staticmethod
    def _required_text(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise TopicSummarizationContractError(
                f"{field_name} must not be empty"
            )
        return value.strip()
