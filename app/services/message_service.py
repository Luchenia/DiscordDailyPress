from datetime import UTC, datetime
from app.dto.discord_message_dto import DiscordMessageDTO
from app.mappers.message_mapper import MessageMapper
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.repositories.message_repository import MessageSaveResult
from app.utils.text_normalizer import normalize
from app.core.logger import get_logger
from app.repositories.message_history_repository import MessageHistoryRepository
from app.repositories.message_delete_history_repository import MessageDeleteHistoryRepository
from app.models.message_history import MessageHistory
from app.models.message_delete_history import MessageDeleteHistory
from app.services.language_service import LanguageService
from app.services.conversation_buffer import ConversationBuffer
from app.dto.conversation_result_dto import ConversationResultDTO
from app.dto.translation_job_dto import TranslationSourceCandidate
from app.database.session import SessionLocal
from app.services.translation_producer_service import TranslationProducerService
from app.utils.content_hash import calculate_source_content_hash


logger = get_logger(__name__)



class MessageService:

    def __init__(
        self,
        translation_producer: TranslationProducerService | None = None,
    ):
        self.repository = MessageRepository()
        self.history_repository = MessageHistoryRepository()
        self.delete_history_repository = MessageDeleteHistoryRepository()
        self.language_service = LanguageService()
        self.translation_producer = translation_producer

        self.conversation_buffer = ConversationBuffer(
            result_handler=self.process_conversation_result
        )

    def save(
        self,
        dto: DiscordMessageDTO,
    ) -> MessageSaveResult | None:

        # 1. Bot Filter
        if dto.is_bot:
            logger.info(
                "Ignored bot message from %s",
                dto.author_display_name,
            )
            return None

        # 2. Normalize
        dto = dto.model_copy(
            update={
                "content": normalize(dto.content)
            }
        )

        # 3. DTO -> Entity
        entity = MessageMapper.dto_to_entity(dto)

        # 4. Save
        save_result = self.repository.save(entity)

        if not save_result.created:
            logger.info(
                "Skipped duplicate message create (Discord: %s)",
                dto.discord_message_id,
            )
            return save_result

        # 5. Conversation Buffer
        session = self.conversation_buffer.add(dto)

        # 6. Log
        logger.info(
            "Saved message #%s from %s",
            save_result.message.id,
            save_result.message.author_display_name,
        )

        logger.info(
            "Conversation session: %s messages",
            len(session.messages),
        )

        return save_result

    def update(
        self,
        dto: DiscordMessageDTO,
    ) -> Message | None:

        # 1. Discord 메시지 ID로 기존 데이터 조회
        with SessionLocal(expire_on_commit=False) as session:
            with session.begin():
                entity = self.repository.get_by_discord_message_id(
                    dto.discord_message_id,
                    session=session,
                )

                if entity is None:
                    logger.warning(
                        "Message %s not found.",
                        dto.discord_message_id,
                    )
                    return None

                history = MessageHistory(
                    message_id=entity.id,
                    discord_message_id=entity.discord_message_id,

                    old_content=entity.content,
                    new_content=normalize(dto.content),

                    edited_at=dto.edited_at or datetime.now(UTC),
                )
                self.history_repository.save(
                    history,
                    session=session,
                )

                entity.content = history.new_content

                entity.language = self.language_service.detect(
                    entity.content
                )

                entity.edited_at = history.edited_at

                updated = self.repository.update(
                    entity,
                    session=session,
                )
                translation_candidate = self._translation_candidate(updated)
        

        # # 2. 내용 정규화
        # entity.content = normalize(dto.content)

        # # 3. 수정 시간 갱신
        # entity.edited_at = dto.edited_at or datetime.now(UTC)

        # # 4. 저장
        # updated = self.repository.update(entity)

        logger.info(
            "Updated message #%s (Discord: %s)",
            updated.id,
            updated.discord_message_id,
        )

        self._enqueue_translation_candidates([translation_candidate])

        return updated


    def delete(
        self,
        discord_message_id: int,
    ) -> bool:

        with SessionLocal.begin() as session:
            entity = self.repository.get_by_discord_message_id(
                discord_message_id,
                session=session,
            )

            if entity is None:
                logger.warning(
                    "Message %s not found.",
                    discord_message_id,
                )
                return False

            if entity.deleted_at is not None:
                logger.info(
                    "Message #%s (Discord: %s) is already deleted.",
                    entity.id,
                    entity.discord_message_id,
                )
                return True

            message_id = entity.id
            message_discord_id = entity.discord_message_id
            deleted_at = datetime.now(UTC)

            history = MessageDeleteHistory(
                message_id=message_id,
                discord_message_id=message_discord_id,

                guild_id=entity.guild_id,
                channel_id=entity.channel_id,

                author_id=entity.author_id,
                author_display_name=entity.author_display_name,

                content=entity.content,

                created_at=entity.created_at,
                deleted_at=deleted_at,
            )

            self.delete_history_repository.save(
                history,
                session=session,
            )

            deleted = self.repository.soft_delete_by_id(
                message_id=message_id,
                deleted_at=deleted_at,
                session=session,
            )

            if not deleted:
                raise RuntimeError(
                    "Message disappeared during soft delete."
                )

        logger.info(
            "Soft-deleted message #%s (Discord: %s)",
            message_id,
            message_discord_id,
        )

        return True

    def update_language(
        self,
        result: ConversationResultDTO,
    ) -> list[TranslationSourceCandidate]:

        success_count = 0
        failure_count = 0
        translation_candidates = []

        with SessionLocal.begin() as session:
            for discord_message_id in result.message_ids:
                message = self.repository.get_by_discord_message_id(
                    discord_message_id,
                    session=session,
                )

                if message is None:
                    failure_count += 1

                    logger.warning(
                        "Message %s not found while updating language.",
                        discord_message_id,
                    )
                    continue

                message.language = self.language_service.detect(
                    message.content
                )
                updated = self.repository.update(
                    message,
                    session=session,
                )
                translation_candidates.append(
                    self._translation_candidate(updated)
                )
                success_count += 1

        logger.info(
            "Source language update completed: %s/%s messages",
            success_count,
            len(result.message_ids),
        )

        return translation_candidates


    def process_conversation_result(
        self,
        result: ConversationResultDTO,
    ) -> None:

        translation_candidates = self.update_language(result)
        self._enqueue_translation_candidates(translation_candidates)

        logger.info(
            "Processed conversation: %s messages, language=%s",
            len(result.message_ids),
            result.language,
        )

    @staticmethod
    def _translation_candidate(message: Message) -> TranslationSourceCandidate:
        return TranslationSourceCandidate(
            message_id=message.id,
            guild_id=message.guild_id,
            channel_id=message.channel_id,
            source_language=message.language,
            source_content_hash=calculate_source_content_hash(message.content),
            deleted_at=message.deleted_at,
        )

    def _enqueue_translation_candidates(
        self,
        candidates: list[TranslationSourceCandidate],
    ) -> None:
        if self.translation_producer is None or not candidates:
            return

        try:
            self.translation_producer.enqueue_candidates(candidates)
        except Exception:
            logger.exception(
                "Translation producer failed for %s message(s)",
                len(candidates),
            )

    async def stop_conversation_cleanup(self) -> None:
        await self.conversation_buffer.stop_cleanup()
