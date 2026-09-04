import asyncio
from unittest.mock import AsyncMock, Mock

import discord
from discord import app_commands

from app.bot.commands.reporter_command import ReporterCommand


def create_command():
    repository = Mock()

    intents = discord.Intents.none()

    client = discord.Client(
        intents=intents,
    )

    tree = app_commands.CommandTree(
        client,
    )

    command = ReporterCommand(
        repository=repository,
    )

    command.register(tree)

    return (
        repository,
        tree,
    )


def create_interaction(
    guild_id: int = 100,
    channel_id: int = 200,
    channel_name: str = "일반",
):
    interaction = Mock()

    interaction.guild = Mock()
    interaction.guild.id = guild_id

    interaction.channel = Mock()
    interaction.channel.id = channel_id
    interaction.channel.name = channel_name

    interaction.user = Mock()
    interaction.user.guild_permissions = Mock()
    interaction.user.guild_permissions.administrator = True

    interaction.response = Mock()
    interaction.response.send_message = AsyncMock()

    return interaction


def test_reporter_command_registers_commands():

    _, tree = create_command()

    command = tree.get_command("기자")

    assert command is not None

    command_names = {
        child.name
        for child in command.commands
    }

    assert command_names == {
        "파견",
        "철수",
        "현황",
    }


def test_reporter_dispatch_adds_new_channel():

    repository, tree = create_command()

    repository.get_by_guild.return_value = []

    channel = Mock()
    channel.id = 200
    channel.name = "일반"

    repository.add.return_value = channel

    interaction = create_interaction()

    command = tree.get_command("기자")
    dispatch = command.get_command("파견")

    asyncio.run(
        dispatch.callback(
            interaction,
        )
    )

    repository.add.assert_called_once()

    added_channel = repository.add.call_args.args[0]

    assert added_channel.guild_id == 100
    assert added_channel.channel_id == 200
    assert added_channel.channel_name == "일반"
    assert added_channel.enabled is True

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "분석 대상 채널 활성화 완료" in message
    assert "일반" in message
    assert "향후 분석에 포함" in message


def test_reporter_dispatch_reactivates_existing_channel():

    repository, tree = create_command()

    existing_channel = Mock()

    existing_channel.guild_id = 100
    existing_channel.channel_id = 200
    existing_channel.channel_name = "일반"
    existing_channel.enabled = False

    repository.get_by_guild.return_value = [
        existing_channel,
    ]

    interaction = create_interaction()

    command = tree.get_command("기자")
    dispatch = command.get_command("파견")

    asyncio.run(
        dispatch.callback(
            interaction,
        )
    )

    repository.enable.assert_called_once_with(
        guild_id=100,
        channel_id=200,
    )

    repository.add.assert_not_called()

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "분석 대상 채널 활성화 완료" in message


def test_reporter_dispatch_rejects_already_active_channel():

    repository, tree = create_command()

    existing_channel = Mock()

    existing_channel.guild_id = 100
    existing_channel.channel_id = 200
    existing_channel.channel_name = "일반"
    existing_channel.enabled = True

    repository.get_by_guild.return_value = [
        existing_channel,
    ]

    interaction = create_interaction()

    command = tree.get_command("기자")
    dispatch = command.get_command("파견")

    asyncio.run(
        dispatch.callback(
            interaction,
        )
    )

    repository.add.assert_not_called()

    repository.enable.assert_not_called()

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "이미 분석 대상으로 활성화" in message


def test_reporter_recall_disables_channel():

    repository, tree = create_command()

    repository.disable.return_value = True

    interaction = create_interaction()

    command = tree.get_command("기자")
    recall = command.get_command("철수")

    asyncio.run(
        recall.callback(
            interaction,
        )
    )

    repository.disable.assert_called_once_with(
        guild_id=100,
        channel_id=200,
    )

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "분석 대상 채널 비활성화 완료" in message
    assert "원본 메시지는 계속 보존" in message


def test_reporter_recall_handles_missing_channel():

    repository, tree = create_command()

    repository.disable.return_value = False

    interaction = create_interaction()

    command = tree.get_command("기자")
    recall = command.get_command("철수")

    asyncio.run(
        recall.callback(
            interaction,
        )
    )

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "분석 대상으로 활성화되어 있지 않습니다" in message


def test_reporter_status_shows_active_channels():

    repository, tree = create_command()

    first = Mock()
    first.channel_name = "일반"
    first.enabled = True

    second = Mock()
    second.channel_name = "잡담"
    second.enabled = True

    third = Mock()
    third.channel_name = "공지"
    third.enabled = False

    repository.get_by_guild.return_value = [
        first,
        second,
        third,
    ]

    interaction = create_interaction()

    command = tree.get_command("기자")
    status = command.get_command("현황")

    asyncio.run(
        status.callback(
            interaction,
        )
    )

    repository.get_by_guild.assert_called_once_with(
        100,
    )

    interaction.response.send_message.assert_called_once()

    embed = (
        interaction.response.send_message.call_args.kwargs["embed"]
    )

    assert embed.title == "📰 분석 대상 채널 현황"

    embed_text = "\n".join(
        field.value
        for field in embed.fields
    )

    assert "#일반" in embed_text
    assert "#잡담" in embed_text
    assert embed.fields[0].name == "활성 분석 대상"


def test_reporter_commands_describe_analysis_target_management():

    _, tree = create_command()

    command = tree.get_command("기자")

    assert command.description == "분석 대상 채널을 관리합니다."
    assert (
        command.get_command("파견").description
        == "현재 채널을 분석 대상으로 활성화합니다."
    )
    assert (
        command.get_command("철수").description
        == "현재 채널을 분석 대상에서 비활성화합니다."
    )


def test_reporter_commands_require_administrator():

    repository, tree = create_command()

    interaction = create_interaction()

    interaction.user.guild_permissions.administrator = False

    command = tree.get_command("기자")
    dispatch = command.get_command("파견")

    asyncio.run(
        dispatch.callback(
            interaction,
        )
    )

    repository.add.assert_not_called()

    interaction.response.send_message.assert_called_once()

    message = (
        interaction.response.send_message.call_args.args[0]
    )

    assert "관리자" in message
