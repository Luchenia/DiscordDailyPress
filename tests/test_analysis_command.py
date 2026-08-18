import asyncio
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import discord

from app.bot.commands.analysis_command import AnalysisCommand

from app.dto.statistics_result_dto import StatisticsResultDTO


KST = ZoneInfo("Asia/Seoul")


def create_command():

    analysis_service = Mock()

    intents = discord.Intents.none()

    client = discord.Client(
        intents=intents,
    )

    tree = discord.app_commands.CommandTree(
        client,
    )

    command = AnalysisCommand(
        analysis_service=analysis_service,
    )

    command.register(tree)

    registered_command = tree.get_command(
        "분석",
    )

    return (
        analysis_service,
        command,
        registered_command,
    )


def create_interaction(
    guild_id: int = 100,
):

    interaction = Mock()

    interaction.guild = Mock()
    interaction.guild.id = guild_id

    interaction.response = Mock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    interaction.response.is_done.return_value = False

    interaction.followup = Mock()
    interaction.followup.send = AsyncMock()

    interaction.locale = discord.Locale.korean

    return interaction


def create_statistics():

    return StatisticsResultDTO(
        message_count=10,
        author_count=2,
        channel_count=2,

        top_authors=[],
        channel_activity=[],

        language_distribution={},

        daily_activity=[],
        hourly_activity=[],

        average_message_length=10.0,
        peak_activity_hour=10,
    )


def get_callback(
    command,
):

    return command.callback


def test_analysis_command_is_registered():

    _, _, command = create_command()

    assert command is not None
    assert command.name == "분석"


def test_analysis_command_has_period_parameter():

    _, _, command = create_command()

    parameters = command.parameters

    assert len(parameters) == 1
    assert parameters[0].name == "period"


def test_analysis_today_calls_service():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "오늘",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_this_week_calls_service():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "이번주",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_this_month_calls_service():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "이번달",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_this_year_calls_service():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "올해",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_custom_period():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "직접입력",
        )
    )

    interaction.response.send_modal.assert_awaited_once()


def test_analysis_custom_period_modal_submit():

    analysis_service, analysis_command, command = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "직접입력",
        )
    )

    interaction.response.send_modal.assert_awaited_once()

    modal = (
        interaction.response.send_modal.call_args.args[0]
    )

    assert modal.command is analysis_command


def test_analysis_custom_period_start_only():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "today",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_custom_period_rejects_invalid_date():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="직접입력",
            start_date="2026/08/01",
        )
    )

    analysis_service.analyze.assert_not_called()

    interaction.response.send_message.assert_awaited_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "YYYY-MM-DD" in message


def test_analysis_custom_period_rejects_end_only():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="직접입력",
            start_date=None,
            end_date="2026-08-14",
        )
    )

    analysis_service.analyze.assert_not_called()


def test_analysis_custom_period_accepts_same_date():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="직접입력",
            start_date="2026-08-14",
            end_date="2026-08-14",
        )
    )

    analysis_service.analyze.assert_called_once()

    request = (
        analysis_service.analyze.call_args.args[0]
    )

    local_start = request.start_at.astimezone(KST)
    local_end = request.end_at.astimezone(KST)

    assert local_start.day == 14
    assert local_end.day == 14


def test_analysis_command_rejects_dm():

    analysis_service, _, command = create_command()

    interaction = create_interaction()

    interaction.guild = None

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "오늘",
        )
    )

    analysis_service.analyze.assert_not_called()

    interaction.response.send_message.assert_awaited_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "서버" in message


def test_analysis_command_handles_analysis_error():

    analysis_service, _, command = create_command()

    analysis_service.analyze.side_effect = ValueError(
        "분석 대상으로 활성화된 채널이 없습니다."
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "오늘",
        )
    )

    interaction.response.defer.assert_awaited_once()

    interaction.followup.send.assert_awaited_once()

    message = (
        interaction.followup.send.call_args.args[0]
    )

    assert message == (
        "분석 대상으로 활성화된 채널이 없습니다."
    )


def test_analysis_command_sends_result_embed():

    analysis_service, _, command = create_command()

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    callback = get_callback(
        command,
    )

    asyncio.run(
        callback(
            interaction,
            "직접입력",
        )
    )

    # 직접입력은 Modal을 열기 때문에
    # 바로 분석 결과 Embed가 전송되지 않는다.
    interaction.response.send_modal.assert_awaited_once()


def test_analysis_period_autocomplete_korean():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = discord.Locale.korean

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]

    assert values == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]


def test_analysis_period_autocomplete_english():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = discord.Locale.american_english

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "today",
        "this week",
        "this month",
        "this year",
        "custom",
    ]

    assert values == [
        "today",
        "this-week",
        "this-month",
        "this-year",
        "custom",
    ]


def test_analysis_period_autocomplete_japanese():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = discord.Locale.japanese

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "今日",
        "今週",
        "今月",
        "今年",
        "カスタム",
    ]

    assert values == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]


def test_analysis_period_autocomplete_chinese_simplified():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = "zh-CN"

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "今天",
        "本周",
        "本月",
        "今年",
        "自定义",
    ]

    assert values == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]


def test_analysis_period_autocomplete_chinese_traditional():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = "zh-TW"

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "今天",
        "本週",
        "本月",
        "今年",
        "自訂",
    ]

    assert values == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]


def test_analysis_period_autocomplete_bulgarian():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = discord.Locale.bulgarian

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    values = [
        choice.value
        for choice in choices
    ]

    assert names == [
        "днес",
        "тази седмица",
        "този месец",
        "тази година",
        "по избор",
    ]

    assert values == [
        "오늘",
        "이번주",
        "이번달",
        "올해",
        "직접입력",
    ]


def test_analysis_period_autocomplete_filters_current_input():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    interaction.locale = discord.Locale.american_english

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "month",
        )
    )

    names = [
        choice.name
        for choice in choices
    ]

    assert names == [
        "this month",
    ]


def test_analysis_period_autocomplete_limits_choices():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    assert len(choices) <= 25


def test_analysis_period_autocomplete_returns_choice_objects():

    _, analysis_command, _ = create_command()

    interaction = create_interaction()

    choices = asyncio.run(
        analysis_command.period_autocomplete(
            interaction,
            "",
        )
    )

    assert all(
        isinstance(
            choice,
            discord.app_commands.Choice,
        )
        for choice in choices
    )


def test_analysis_command_maps_english_period():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="today",
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_command_maps_custom_period():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="custom",
            start_date="2026-08-01",
            end_date="2026-08-14",
        )
    )

    analysis_service.analyze.assert_called_once()

    request = (
        analysis_service.analyze.call_args.args[0]
    )

    local_start = request.start_at.astimezone(KST)
    local_end = request.end_at.astimezone(KST)

    assert local_start.year == 2026
    assert local_start.month == 8
    assert local_start.day == 1

    assert local_end.year == 2026
    assert local_end.month == 8
    assert local_end.day == 14


def test_analysis_command_output_language_is_korean():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    interaction = create_interaction()

    asyncio.run(
        analysis_command._run_analysis(
            interaction=interaction,
            period="오늘",
        )
    )

    request = (
        analysis_service.analyze.call_args.args[0]
    )

    assert request.output_language == "ko"


def test_custom_period_modal_fields():

    _, analysis_command, _ = create_command()

    from app.bot.commands.analysis_command import (
        CustomPeriodModal,
    )

    modal = CustomPeriodModal(
        analysis_command,
    )

    assert modal.title == "분석 기간 직접 입력"

    assert len(modal.children) == 2

    start_date = modal.children[0]
    end_date = modal.children[1]

    assert start_date.label == "시작일"
    assert start_date.placeholder == "YYYY-MM-DD"
    assert start_date.required is True
    assert start_date.max_length == 10

    assert end_date.label == "종료일"
    assert end_date.placeholder == "YYYY-MM-DD (선택)"
    assert end_date.required is False
    assert end_date.max_length == 10


def test_analysis_custom_period_modal_submit():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    from app.bot.commands.analysis_command import (
        CustomPeriodModal,
    )

    modal = CustomPeriodModal(
        analysis_command,
    )

    modal.start_date._value = "2026-08-01"
    modal.end_date._value = "2026-08-14"

    interaction = create_interaction()

    interaction.response.is_done.return_value = True

    asyncio.run(
        modal.on_submit(
            interaction,
        )
    )

    analysis_service.analyze.assert_called_once()

    request = (
        analysis_service.analyze.call_args.args[0]
    )

    local_start = request.start_at.astimezone(KST)
    local_end = request.end_at.astimezone(KST)

    assert local_start.year == 2026
    assert local_start.month == 8
    assert local_start.day == 1

    assert local_end.year == 2026
    assert local_end.month == 8
    assert local_end.day == 14


def test_analysis_custom_period_modal_submit_without_end_date():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    analysis_service.analyze.return_value = (
        create_statistics()
    )

    from app.bot.commands.analysis_command import (
        CustomPeriodModal,
    )

    modal = CustomPeriodModal(
        analysis_command,
    )

    modal.start_date._value = "2026-08-01"
    modal.end_date._value = ""

    interaction = create_interaction()

    interaction.response.is_done.return_value = True

    asyncio.run(
        modal.on_submit(
            interaction,
        )
    )

    analysis_service.analyze.assert_called_once()


def test_analysis_custom_period_modal_invalid_date():

    analysis_service, analysis_command, _ = (
        create_command()
    )

    from app.bot.commands.analysis_command import (
        CustomPeriodModal,
    )

    modal = CustomPeriodModal(
        analysis_command,
    )

    modal.start_date._value = "2026/08/01"
    modal.end_date._value = ""

    interaction = create_interaction()

    interaction.response.is_done.return_value = True

    asyncio.run(
        modal.on_submit(
            interaction,
        )
    )

    analysis_service.analyze.assert_not_called()

    interaction.followup.send.assert_awaited_once()

    message = (
        interaction.followup.send.call_args.args[0]
    )

    assert "YYYY-MM-DD" in message


def datetime_now_kst():

    from datetime import datetime, timezone

    return datetime.now(
        timezone.utc,
    ).astimezone(KST)