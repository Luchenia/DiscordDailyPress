import discord
from discord.ext import commands

from app.collectors.message_collector import MessageCollector


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

    async def on_ready(self):

        print(f"Logged in as {self.user}")

    async def on_message(
        self,
        message: discord.Message,
    ):

        await self.message_collector.collect(message)

        await self.process_commands(message)