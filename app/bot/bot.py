import discord
from discord.ext import commands

from app.bot.commands.analysis_command import AnalysisCommand
from app.bot.commands.reporter_command import ReporterCommand
from app.collectors.message_collector import MessageCollector
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)
from app.services.analysis_service import AnalysisService
from app.core.config import config

from app.bot.localization import ChronicleTranslator


class ChronicleBot(commands.Bot):

    def __init__(self):

        intents = discord.Intents.default()

        intents.message_content = True
        intents.guilds = True
        intents.messages = True

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

        self.message_collector = MessageCollector()

        self.analysis_service = AnalysisService()

        self.analysis_command = AnalysisCommand(
            analysis_service=self.analysis_service,
        )

        self.reporter_command = ReporterCommand(
            repository=CollectionChannelRepository(),
        )

    async def setup_hook(self):

        await self.tree.set_translator(
            ChronicleTranslator(),
        )

        self.analysis_command.register(
            self.tree,
        )

        self.reporter_command.register(
            self.tree,
        )

        guild = discord.Object(
            id=config.discord_guild_id,
        )

        # 현재 코드에 등록된 명령어를 테스트 서버로 복사
        self.tree.copy_global_to(
            guild=guild,
        )

        # 기존 글로벌 명령어 제거
        self.tree.clear_commands(
            guild=None,
        )

        # Discord의 글로벌 명령어도 삭제
        await self.tree.sync()

        # 테스트 서버에만 명령어 등록
        await self.tree.sync(
            guild=guild,
        )

        print("Guild slash commands synchronized.")

    async def on_ready(self):

        print(f"Logged in as {self.user}")

        self.message_collector.start_cleanup()

    async def on_message(
        self,
        message: discord.Message,
    ):

        await self.message_collector.collect(
            message,
        )

        await self.process_commands(
            message,
        )

    async def on_raw_message_edit(
        self,
        payload: discord.RawMessageUpdateEvent,
    ):

        channel = self.get_channel(
            payload.channel_id,
        )

        if channel is None:

            try:

                channel = await self.fetch_channel(
                    payload.channel_id,
                )

            except discord.NotFound:

                return

            except discord.Forbidden:

                return

        try:

            message = await channel.fetch_message(
                payload.message_id,
            )

        except discord.NotFound:

            return

        except discord.Forbidden:

            return

        await self.message_collector.collect_edit(
            None,
            message,
        )

    async def on_raw_message_delete(
        self,
        payload: discord.RawMessageDeleteEvent,
    ):

        await self.message_collector.collect_raw_delete(
            payload,
        )