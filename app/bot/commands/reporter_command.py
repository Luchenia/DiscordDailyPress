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
                "분석 대상 채널을 관리합니다."
            ),
        )

        @reporter_group.command(
            name=app_commands.locale_str("파견"),
            description=app_commands.locale_str(
                "현재 채널을 분석 대상으로 활성화합니다."
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
                        f"📰 이미 분석 대상으로 활성화된 채널입니다.\n\n"
                        f"📍 분석 대상: #{channel_name}",
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
                f"📰 **분석 대상 채널 활성화 완료**\n\n"
                f"📍 분석 대상: #{channel_name}\n\n"
                f"이 채널의 수집된 원본 메시지가 향후 분석에 포함됩니다.",
            )

        @reporter_group.command(
            name=app_commands.locale_str("철수"),
            description=app_commands.locale_str(
                "현재 채널을 분석 대상에서 비활성화합니다."
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
                    "📭 이 채널은 분석 대상으로 활성화되어 있지 않습니다.",
                    ephemeral=True,
                )

                return

            await interaction.response.send_message(
                f"📰 **분석 대상 채널 비활성화 완료**\n\n"
                f"📍 분석 대상: #{interaction.channel.name}\n\n"
                f"원본 메시지는 계속 보존되며, 이 채널은 향후 분석에서 제외됩니다.",
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
                title="📰 분석 대상 채널 현황",
                description=(
                    "현재 분석에 포함되는 활성 채널입니다."
                ),
            )

            if active_channels:

                locations = "\n".join(
                    f"📍 #{channel.channel_name}"
                    for channel in active_channels
                )

                embed.add_field(
                    name="활성 분석 대상",
                    value=locations,
                    inline=False,
                )

                embed.set_footer(
                    text=(
                        f"활성 분석 채널: "
                        f"{len(active_channels)}개"
                    ),
                )

            else:

                embed.add_field(
                    name="활성 분석 대상",
                    value="활성 분석 대상 채널이 없습니다.",
                    inline=False,
                )

                embed.set_footer(
                    text="활성 분석 채널: 0개",
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
