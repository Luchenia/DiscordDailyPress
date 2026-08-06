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

        if message.author.bot:
            return

        if message.guild is None:
            return

        dto = DiscordMessageDTO(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            author_id=message.author.id,
            author_name=message.author.display_name,
            content=message.content,
            created_at=message.created_at,
        )

        self.service.save(dto)