from app.dto.discord_message_dto import DiscordMessageDTO
from app.models.message import Message


class MessageMapper:

    @staticmethod
    def dto_to_entity(
        dto: DiscordMessageDTO,
        language: str | None = None,
    ) -> Message:

        return Message(
            guild_id=dto.guild_id,
            channel_id=dto.channel_id,
            author_id=dto.author_id,
            author_name=dto.author_name,
            content=dto.content,
            language=language,
            created_at=dto.created_at,
        )