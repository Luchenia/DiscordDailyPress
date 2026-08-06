from app.dto.discord_message_dto import DiscordMessageDTO
from app.mappers.message_mapper import MessageMapper
from app.models.message import Message
from app.repositories.message_repository import MessageRepository
from app.utils.text_normalizer import normalize
from app.core.logger import get_logger

logger = get_logger(__name__)



class MessageService:

    def __init__(self):
        self.repository = MessageRepository()

    def save(
        self,
        dto: DiscordMessageDTO,
    ) -> Message:

        # 비즈니스 로직
        dto = dto.model_copy(
            update={
                "content": normalize(dto.content)
            }
        )

        entity = MessageMapper.dto_to_entity(dto)

        saved = self.repository.save(entity)

        logger.info(
            "Saved message #%s from %s",
            saved.id,
            saved.author_name,
        )

        return saved