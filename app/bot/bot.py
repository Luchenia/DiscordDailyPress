import asyncio

import discord
from discord.ext import commands

from app.bot.commands.analysis_command import AnalysisCommand
from app.bot.commands.reporter_command import ReporterCommand
from app.collectors.message_collector import MessageCollector
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)
from app.services.analysis_service import AnalysisService
from app.services.translation_provider import TranslationProvider
from app.services.translation_queue_service import TranslationQueueService
from app.services.translation_worker import TranslationWorker
from app.core.config import config
from app.core.logger import get_logger

from app.bot.localization import ChronicleTranslator

logger = get_logger(__name__)


class ChronicleBot(commands.Bot):

    TRANSLATION_DRAIN_TIMEOUT_SECONDS = 5

    def __init__(
        self,
        translation_provider: TranslationProvider | None = None,
    ):

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

        self.translation_queue: TranslationQueueService | None = None
        self.translation_worker: TranslationWorker | None = None
        self._accepting_translation_jobs = False
        self._translation_closing = False

        if translation_provider is not None:
            self.translation_queue = TranslationQueueService(maxsize=100)
            self.translation_worker = TranslationWorker(
                self.translation_queue,
                translation_provider,
            )

    @property
    def accepts_translation_jobs(self) -> bool:
        return self._accepting_translation_jobs

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

        if self.translation_worker is not None and not self._translation_closing:
            self.translation_worker.start()
            self._accepting_translation_jobs = True

    async def on_ready(self):

        print(f"Logged in as {self.user}")

        self.message_collector.start_cleanup()

    async def close(self):

        self._translation_closing = True
        self._accepting_translation_jobs = False

        try:

            try:

                await self._shutdown_translation()

            except Exception:

                logger.exception("Translation shutdown failed")

        finally:

            try:

                try:

                    await self.message_collector.stop_cleanup()

                except Exception:

                    logger.exception("Conversation buffer shutdown failed")

            finally:

                await super().close()

    async def _shutdown_translation(self):

        if self.translation_queue is None or self.translation_worker is None:
            return

        try:

            try:

                await asyncio.wait_for(
                    self.translation_queue.join(),
                    timeout=self.TRANSLATION_DRAIN_TIMEOUT_SECONDS,
                )

            except asyncio.TimeoutError:

                logger.warning(
                    "Translation queue did not drain within %s seconds",
                    self.TRANSLATION_DRAIN_TIMEOUT_SECONDS,
                )

        finally:

            await self.translation_worker.stop()

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
