import discord
from discord import app_commands

from app.models.collection_channel import CollectionChannel
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)


class ReporterCommand:

    def __init__(
        self,
        repository: CollectionChannelRepository,
    ):
        self.repository = repository

    def register(
        self,
        tree: app_commands.CommandTree,
    ):

        reporter_group = app_commands.Group(
            name=app_commands.locale_str("기자"),
            description=app_commands.locale_str(
                "기자를 파견하고 관리합니다."
            ),
        )

        @reporter_group.command(
            name=app_commands.locale_str("파견"),
            description=app_commands.locale_str(
                "현재 채널에 기자를 파견합니다."
            ),
        )
        async def dispatch(
            interaction: discord.Interaction,
        ):

            if not self._is_admin(interaction):

                await interaction.response.send_message(
                    "이 명령어는 서버 관리자만 사용할 수 있습니다.",
                    ephemeral=True,
                )

                return

            if interaction.guild is None:

                await interaction.response.send_message(
                    "서버에서만 사용할 수 있는 명령어입니다.",
                    ephemeral=True,
                )

                return

            if interaction.channel is None:

                await interaction.response.send_message(
                    "현재 채널을 확인할 수 없습니다.",
                    ephemeral=True,
                )

                return

            guild_id = interaction.guild.id
            channel_id = interaction.channel.id
            channel_name = interaction.channel.name

            channels = self.repository.get_by_guild(
                guild_id,
            )

            existing_channel = next(
                (
                    channel
                    for channel in channels
                    if channel.channel_id == channel_id
                ),
                None,
            )

            if existing_channel is not None:

                if existing_channel.enabled:

                    await interaction.response.send_message(
                        f"📰 이미 파견된 기자가 있습니다.\n\n"
                        f"📍 파견지: #{channel_name}",
                        ephemeral=True,
                    )

                    return

                self.repository.enable(
                    guild_id=guild_id,
                    channel_id=channel_id,
                )

            else:

                channel = CollectionChannel(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    channel_name=channel_name,
                    enabled=True,
                )

                self.repository.add(
                    channel,
                )

            await interaction.response.send_message(
                f"📰 **기자 파견 완료**\n\n"
                f"📍 파견지: #{channel_name}\n\n"
                f"이제부터 해당 채널의 소식을 취재합니다.",
            )

        @reporter_group.command(
            name=app_commands.locale_str("철수"),
            description=app_commands.locale_str(
                "현재 채널에서 기자를 철수시킵니다."
            ),
        )
        async def recall(
            interaction: discord.Interaction,
        ):

            if not self._is_admin(interaction):

                await interaction.response.send_message(
                    "이 명령어는 서버 관리자만 사용할 수 있습니다.",
                    ephemeral=True,
                )

                return

            if interaction.guild is None:

                await interaction.response.send_message(
                    "서버에서만 사용할 수 있는 명령어입니다.",
                    ephemeral=True,
                )

                return

            if interaction.channel is None:

                await interaction.response.send_message(
                    "현재 채널을 확인할 수 없습니다.",
                    ephemeral=True,
                )

                return

            success = self.repository.disable(
                guild_id=interaction.guild.id,
                channel_id=interaction.channel.id,
            )

            if not success:

                await interaction.response.send_message(
                    "📭 이곳에는 파견된 기자가 없습니다.",
                    ephemeral=True,
                )

                return

            await interaction.response.send_message(
                f"📰 **기자 철수 완료**\n\n"
                f"📍 파견지: #{interaction.channel.name}\n\n"
                f"해당 채널의 취재를 중단합니다.",
            )

        @reporter_group.command(
            name=app_commands.locale_str("현황"),
            description=app_commands.locale_str(
                "현재 기자들의 파견지를 확인합니다."
            ),
        )
        async def status(
            interaction: discord.Interaction,
        ):

            if interaction.guild is None:

                await interaction.response.send_message(
                    "서버에서만 사용할 수 있는 명령어입니다.",
                    ephemeral=True,
                )

                return

            channels = self.repository.get_by_guild(
                interaction.guild.id,
            )

            active_channels = [
                channel
                for channel in channels
                if channel.enabled
            ]

            embed = discord.Embed(
                title="📰 파견지 현황",
                description=(
                    "현재 기자들이 파견된 채널입니다."
                ),
            )

            if active_channels:

                locations = "\n".join(
                    f"📍 #{channel.channel_name}"
                    for channel in active_channels
                )

                embed.add_field(
                    name="현재 파견지",
                    value=locations,
                    inline=False,
                )

                embed.set_footer(
                    text=(
                        f"파견 기자: "
                        f"{len(active_channels)}명"
                    ),
                )

            else:

                embed.add_field(
                    name="현재 파견지",
                    value="현재 파견된 기자가 없습니다.",
                    inline=False,
                )

                embed.set_footer(
                    text="파견 기자: 0명",
                )

            await interaction.response.send_message(
                embed=embed,
            )

        tree.add_command(
            reporter_group,
        )

    @staticmethod
    def _is_admin(
        interaction: discord.Interaction,
    ) -> bool:

        if interaction.guild is None:
            return False

        if interaction.user is None:
            return False

        return interaction.user.guild_permissions.administrator