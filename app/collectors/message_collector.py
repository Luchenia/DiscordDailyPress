import discord

from app.core.logger import get_logger
from app.dto.discord_message_dto import DiscordMessageDTO
from app.services.message_service import MessageService

logger = get_logger(__name__)


class MessageCollector:

    def __init__(self):
        self.service = MessageService()

    async def collect(
        self,
        message: discord.Message,
    ):

        # if message.author.bot:
        #     return

        if message.guild is None:
            return

        dto = DiscordMessageDTO(
            # Discord 원본
            discord_message_id=message.id,

            guild_id=message.guild.id,
            guild_name=message.guild.name,

            channel_id=message.channel.id,
            channel_name=message.channel.name,

            # 작성자
            author_id=message.author.id,
            author_username=message.author.name,
            author_display_name=message.author.display_name,

            is_bot=message.author.bot,

            # 메시지
            content=message.content,

            # 첨부파일
            has_attachment=len(message.attachments) > 0,
            attachment_count=len(message.attachments),

            # 답글
            reply_to_message_id=(
                message.reference.message_id
                if message.reference
                else None
            ),

            # 시간
            created_at=message.created_at,
            edited_at=message.edited_at,
        )

        self.service.save(dto)


    async def collect_edit(
        self,
        before: discord.Message,
        after: discord.Message,
    ):
        logger.info(
                    "collect_edit called: %s",
                    after.id,
                )

        if after.guild is None:
            return

        dto = DiscordMessageDTO(
            # Discord 원본
            discord_message_id=after.id,

            guild_id=after.guild.id,
            guild_name=after.guild.name,

            channel_id=after.channel.id,
            channel_name=after.channel.name,

            # 작성자
            author_id=after.author.id,
            author_username=after.author.name,
            author_display_name=after.author.display_name,

            is_bot=after.author.bot,

            # 메시지
            content=after.content,

            # 첨부파일
            has_attachment=len(after.attachments) > 0,
            attachment_count=len(after.attachments),

            # 답글
            reply_to_message_id=(
                after.reference.message_id
                if after.reference
                else None
            ),

            # 시간
            created_at=after.created_at,
            edited_at=after.edited_at,
        )

        self.service.update(dto)


    async def collect_delete(
        self,
        message: discord.Message,
    ):

        if message.guild is None:
            return

        self.service.delete(
            message.id
        )


    def start_cleanup(self):
        self.service.conversation_buffer.start_cleanup()