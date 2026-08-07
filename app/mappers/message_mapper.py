from app.dto.discord_message_dto import DiscordMessageDTO
from app.models.message import Message


class MessageMapper:

    @staticmethod
    def dto_to_entity(
        dto: DiscordMessageDTO,
        language: str | None = None,
    ) -> Message:

        return Message(
            discord_message_id=dto.discord_message_id,

            guild_id=dto.guild_id,
            guild_name=dto.guild_name,

            channel_id=dto.channel_id,
            channel_name=dto.channel_name,

            author_id=dto.author_id,
            author_username=dto.author_username,
            author_display_name=dto.author_display_name,

            is_bot=dto.is_bot,

            content=dto.content,

            language=language or "unknown",

            has_attachment=dto.has_attachment,
            attachment_count=dto.attachment_count,

            reply_to_message_id=dto.reply_to_message_id,

            created_at=dto.created_at,
            edited_at=dto.edited_at,
        )