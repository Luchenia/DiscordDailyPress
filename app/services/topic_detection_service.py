from app.dto.analysis_dataset_dto import AnalysisDatasetDTO
from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.topic_detection_dto import (
    DetectedTopicDTO,
    TopicDetectionMessageDTO,
    TopicDetectionResultDTO,
    TopicMembershipDTO,
)
from app.services.topic_detection_provider import TopicDetectionProvider


class TopicDetectionContractError(ValueError):
    """Raised when a dataset or provider proposal violates identity contracts."""


class TopicDetectionService:
    """Prepare safe topic inputs and materialize provider-proposed membership."""

    def __init__(self, provider: TopicDetectionProvider):
        self.provider = provider

    async def detect_topics(
        self,
        dataset: AnalysisDatasetDTO,
    ) -> TopicDetectionResultDTO:
        detector_id = self.provider.detector_id.strip()
        if not detector_id:
            raise TopicDetectionContractError("detector_id must not be empty")

        messages = tuple(
            self._to_topic_message(message)
            for message in dataset.messages
        )
        messages_by_id = {message.message_id: message for message in messages}
        if len(messages_by_id) != len(messages):
            raise TopicDetectionContractError(
                "analysis dataset contains duplicate message IDs"
            )

        if not messages:
            return TopicDetectionResultDTO(
                scope=dataset.scope,
                detector_id=detector_id,
                topics=[],
                unassigned_messages=[],
            )

        proposal = await self.provider.detect_topics(messages)
        topic_ids = [topic.topic_id for topic in proposal.topics]
        if len(topic_ids) != len(set(topic_ids)):
            raise TopicDetectionContractError(
                "provider returned duplicate topic IDs"
            )

        proposed_message_ids = [
            message_id
            for topic in proposal.topics
            for message_id in topic.message_ids
        ] + proposal.unassigned_message_ids
        if len(proposed_message_ids) != len(set(proposed_message_ids)):
            raise TopicDetectionContractError(
                "provider assigned a message more than once"
            )

        known_message_ids = set(messages_by_id)
        proposed_ids = set(proposed_message_ids)
        unknown_ids = proposed_ids - known_message_ids
        if unknown_ids:
            raise TopicDetectionContractError(
                "provider returned message IDs outside the analysis dataset: "
                + ", ".join(str(message_id) for message_id in sorted(unknown_ids))
            )

        missing_ids = known_message_ids - proposed_ids
        if missing_ids:
            raise TopicDetectionContractError(
                "provider omitted analysis message IDs: "
                + ", ".join(str(message_id) for message_id in sorted(missing_ids))
            )

        topics = [
            DetectedTopicDTO(
                topic_id=topic.topic_id,
                label=topic.label,
                memberships=[
                    TopicMembershipDTO(
                        topic_id=topic.topic_id,
                        message=messages_by_id[message_id],
                    )
                    for message_id in topic.message_ids
                ],
            )
            for topic in proposal.topics
        ]
        unassigned_messages = [
            messages_by_id[message_id]
            for message_id in proposal.unassigned_message_ids
        ]

        return TopicDetectionResultDTO(
            scope=dataset.scope,
            detector_id=detector_id,
            topics=topics,
            unassigned_messages=unassigned_messages,
        )

    @staticmethod
    def _to_topic_message(
        message: AnalysisMessageDTO,
    ) -> TopicDetectionMessageDTO:
        return TopicDetectionMessageDTO(
            message_id=message.message_id,
            guild_id=message.guild_id,
            channel_id=message.channel_id,
            channel_name=message.channel_name,
            author_id=message.author_id,
            author_display_name=message.author_display_name,
            analysis_content=message.analysis_content,
            analysis_language=message.analysis_language,
            source_language=message.language,
            analysis_content_source=message.analysis_content_source,
            source_content_hash=message.source_content_hash,
            translation_id=message.translation_id,
            created_at=message.created_at,
        )
