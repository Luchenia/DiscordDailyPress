from datetime import UTC, datetime
from app.dto.discord_message_dto import DiscordMessageDTO
from app.mappers.message_mapper import MessageMapper
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.utils.text_normalizer import normalize
from app.core.logger import get_logger
from app.repositories.message_history_repository import MessageHistoryRepository
from app.repositories.message_delete_history_repository import MessageDeleteHistoryRepository
from app.models.message_history import MessageHistory
from app.models.message_delete_history import MessageDeleteHistory
from app.services.language_service import LanguageService


logger = get_logger(__name__)



class MessageService:

    def __init__(self):
        self.repository = MessageRepository()
        self.history_repository = MessageHistoryRepository()
        self.delete_history_repository = MessageDeleteHistoryRepository()
        self.language_service = LanguageService()

    def save(
        self,
        dto: DiscordMessageDTO,
    ) -> Message | None:

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

        entity.language = self.language_service.detect(
            entity.content
        )

        # 4. Save
        saved = self.repository.save(entity)

        # 5. Log
        logger.info(
            "Saved message #%s from %s",
            saved.id,
            saved.author_display_name,
        )

        return saved

    def update(
        self,
        dto: DiscordMessageDTO,
    ) -> Message | None:

        # 1. Discord 메시지 ID로 기존 데이터 조회
        entity = self.repository.get_by_discord_message_id(
            dto.discord_message_id
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

            version=1,   # 일단 고정, 다음 Sprint에서 자동 증가

            old_content=entity.content,
            new_content=normalize(dto.content),

            edited_at=dto.edited_at or datetime.now(UTC),
        )
        self.history_repository.save(history)

        entity.content = history.new_content

        entity.language = self.language_service.detect(
            entity.content
        )

        entity.edited_at = history.edited_at

        updated = self.repository.update(entity)
        

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

        return updated


    def delete(
        self,
        discord_message_id: int,
    ) -> bool:

        entity = self.repository.get_by_discord_message_id(
            discord_message_id
        )

        if entity is None:
            logger.warning(
                "Message %s not found.",
                discord_message_id,
            )
            return False

        history = MessageDeleteHistory(
            message_id=entity.id,
            discord_message_id=entity.discord_message_id,

            guild_id=entity.guild_id,
            channel_id=entity.channel_id,

            author_id=entity.author_id,
            author_display_name=entity.author_display_name,

            content=entity.content,

            created_at=entity.created_at,
            deleted_at=datetime.now(UTC),
        )

        self.delete_history_repository.save(history)

        self.repository.delete_by_id(entity.id)

        logger.info(
            "Deleted message #%s (Discord: %s)",
            entity.id,
            entity.discord_message_id,
        )

        return True