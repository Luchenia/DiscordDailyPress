from datetime import UTC, datetime

import discord
from discord import app_commands

from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.services.analysis_period_service import (
    AnalysisPeriodService,
)
from app.services.analysis_service import AnalysisService
from app.utils.datetime_utils import to_kst



class CustomPeriodModal(discord.ui.Modal):

    def __init__(
        self,
        command: "AnalysisCommand",
    ):
        super().__init__(
            title="분석 기간 직접 입력",
        )

        self.command = command

        self.start_date = discord.ui.TextInput(
            label="시작일",
            placeholder="YYYY-MM-DD",
            required=True,
            max_length=10,
        )

        self.end_date = discord.ui.TextInput(
            label="종료일",
            placeholder="YYYY-MM-DD (선택)",
            required=False,
            max_length=10,
        )

        self.add_item(
            self.start_date,
        )

        self.add_item(
            self.end_date,
        )

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):

        await self.command._run_analysis(
            interaction=interaction,
            period="직접입력",
            start_date=self.start_date.value,
            end_date=self.end_date.value or None,
        )


class AnalysisCommand:

    def __init__(
        self,
        analysis_service: AnalysisService,
    ):
        self.analysis_service = analysis_service

        self.period_service = AnalysisPeriodService()

    def register(
        self,
        tree: app_commands.CommandTree,
    ):

        @tree.command(
            name=app_commands.locale_str("분석"),
            description=app_commands.locale_str(
                "서버 대화 통계를 분석합니다."
            ),
        )
        @app_commands.describe(
            period=app_commands.locale_str(
                "분석할 기간을 선택합니다."
            ),
        )
        @app_commands.rename(
            period=app_commands.locale_str(
                "분석기간",
            ),
        )
        @app_commands.autocomplete(
            period=self.period_autocomplete,
        )
        async def analysis(
            interaction: discord.Interaction,
            period: str,
        ):

            if period == "직접입력":

                await interaction.response.send_modal(
                    CustomPeriodModal(
                        self,
                    ),
                )

                return

            await self._run_analysis(
                interaction=interaction,
                period=period,
            )

    async def period_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:

        locale = interaction.locale

        options = self._get_period_options(
            locale,
        )

        current_lower = current.lower()

        return [
            app_commands.Choice(
                name=name,
                value=value,
            )
            for value, name in options
            if (
                not current_lower
                or current_lower in name.lower()
            )
        ][:25]

    @staticmethod
    def _get_period_options(
        locale: discord.Locale,
    ) -> list[tuple[str, str]]:

        language = str(locale)

        if language.startswith("en"):
            return [
                ("today", "today"),
                ("this-week", "this week"),
                ("this-month", "this month"),
                ("this-year", "this year"),
                ("custom", "custom"),
            ]

        if language.startswith("ja"):
            return [
                ("오늘", "今日"),
                ("이번주", "今週"),
                ("이번달", "今月"),
                ("올해", "今年"),
                ("직접입력", "カスタム"),
            ]

        if language.startswith("zh-TW"):
            return [
                ("오늘", "今天"),
                ("이번주", "本週"),
                ("이번달", "本月"),
                ("올해", "今年"),
                ("직접입력", "自訂"),
            ]

        if language.startswith("zh"):
            return [
                ("오늘", "今天"),
                ("이번주", "本周"),
                ("이번달", "本月"),
                ("올해", "今年"),
                ("직접입력", "自定义"),
            ]

        if language.startswith("bg"):
            return [
                ("오늘", "днес"),
                ("이번주", "тази седмица"),
                ("이번달", "този месец"),
                ("올해", "тази година"),
                ("직접입력", "по избор"),
            ]

        return [
            ("오늘", "오늘"),
            ("이번주", "이번주"),
            ("이번달", "이번달"),
            ("올해", "올해"),
            ("직접입력", "직접입력"),
        ]

    async def _run_analysis(
        self,
        interaction: discord.Interaction,
        period: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "서버에서만 사용할 수 있는 명령어입니다.",
                ephemeral=True,
            )

            return

        now = datetime.now(UTC)

        try:

            period_map = {
                "today": "오늘",
                "this-week": "이번주",
                "this-month": "이번달",
                "this-year": "올해",
                "custom": "직접입력",
            }

            period = period_map.get(
                period,
                period,
            )

            start_at, end_at = (
                self.period_service.resolve(
                    period=period,
                    now=now,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            request = AnalysisRequestDTO(
                guild_id=interaction.guild.id,
                start_at=start_at,
                end_at=end_at,
                output_language="ko",
            )

        except ValueError as error:

            if interaction.response.is_done():

                await interaction.followup.send(
                    str(error),
                    ephemeral=True,
                )

            else:

                await interaction.response.send_message(
                    str(error),
                    ephemeral=True,
                )

            return

        if not interaction.response.is_done():

            await interaction.response.defer()

        try:

            statistics = self.analysis_service.analyze(
                request,
            )

        except ValueError as error:

            await interaction.followup.send(
                str(error),
                ephemeral=True,
            )

            return

        # ==========================
        # 분석 기간
        # ==========================

        local_start = to_kst(start_at)
        local_end = to_kst(end_at)

        embed = discord.Embed(
            title="📊 서버 대화 분석",
            description=(
                f"{local_start:%Y-%m-%d}"
                f" ~ "
                f"{local_end:%Y-%m-%d}"
            ),
        )

        # ==========================
        # 기본 통계
        # ==========================

        embed.add_field(
            name="기본 통계",
            value=(
                f"메시지: {statistics.message_count}\n"
                f"작성자: {statistics.author_count}\n"
                f"채널: {statistics.channel_count}"
            ),
            inline=False,
        )

        # ==========================
        # 활동 요약
        # ==========================

        summary_lines = []

        if statistics.peak_activity_date is not None:

            summary_lines.append(
                f"📅 가장 활발한 날짜: "
                f"{statistics.peak_activity_date}"
                f" ({statistics.peak_activity_date_count}개)"
            )

        if statistics.peak_activity_hour is not None:

            summary_lines.append(
                f"⏰ 가장 활발한 시간대: "
                f"{statistics.peak_activity_hour:02d}시"
            )

        summary_lines.append(
            f"📝 평균 메시지 길이: "
            f"{statistics.average_message_length:.1f}자"
        )

        if summary_lines:

            embed.add_field(
                name="📈 활동 요약",
                value="\n".join(
                    summary_lines,
                ),
                inline=False,
            )

        # ==========================
        # 상위 작성자
        # ==========================

        if statistics.top_authors:

            author_text = "\n".join(
                f"{author.author_display_name}: "
                f"{author.message_count}"
                for author in statistics.top_authors[:10]
            )

            embed.add_field(
                name="👤 상위 작성자",
                value=author_text,
                inline=False,
            )

        # ==========================
        # 채널 활동
        # ==========================

        if statistics.channel_activity:

            channel_text = "\n".join(
                f"{channel.channel_name}: "
                f"{channel.message_count}"
                for channel in statistics.channel_activity[:10]
            )

            embed.add_field(
                name="💬 채널 활동",
                value=channel_text,
                inline=False,
            )

        # ==========================
        # 일별 활동
        # ==========================

        if statistics.daily_activity:

            daily_sorted = sorted(
                statistics.daily_activity,
                key=lambda item: (
                    item.message_count,
                    item.date,
                ),
                reverse=True,
            )

            daily_lines = []

            for daily in daily_sorted[:10]:

                daily_lines.append(
                    f"`{daily.date}` "
                    f"{self._make_bar(daily.message_count)} "
                    f"{daily.message_count}"
                )

            embed.add_field(
                name="📅 일별 활동",
                value="\n".join(
                    daily_lines,
                ),
                inline=False,
            )

        # ==========================
        # 시간대별 활동
        # ==========================

        if statistics.hourly_activity:

            hourly_sorted = sorted(
                statistics.hourly_activity,
                key=lambda item: (
                    item.message_count,
                    item.hour,
                ),
                reverse=True,
            )

            hourly_lines = []

            for hourly in hourly_sorted[:10]:

                hourly_lines.append(
                    f"`{hourly.hour:02d}시` "
                    f"{self._make_bar(hourly.message_count)} "
                    f"{hourly.message_count}"
                )

            embed.add_field(
                name="⏰ 시간대별 활동",
                value="\n".join(
                    hourly_lines,
                ),
                inline=False,
            )

        # ==========================
        # 언어 분포
        # ==========================

        if statistics.language_distribution:

            language_text = "\n".join(
                f"{language}: {ratio:.2%}"
                for language, ratio in (
                    statistics.language_distribution.items()
                )
            )

            embed.add_field(
                name="🌐 언어 분포",
                value=language_text,
                inline=False,
            )

        await interaction.followup.send(
            embed=embed,
        )

    @staticmethod
    def _make_bar(
        value: int,
        max_length: int = 10,
    ) -> str:

        if value <= 0:

            return ""

        bar_length = min(
            value,
            max_length,
        )

        return "▮" * bar_length
