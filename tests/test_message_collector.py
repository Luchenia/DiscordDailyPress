import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app.collectors.message_collector import MessageCollector


def create_guild_message(channel_id: int = 200) -> Mock:
    message = Mock()

    message.id = 1

    message.guild = Mock()
    message.guild.id = 100
    message.guild.name = "Test Guild"

    message.channel = Mock()
    message.channel.id = channel_id
    message.channel.name = "비활성-분석-채널"

    message.author = Mock()
    message.author.id = 10
    message.author.name = "test-user"
    message.author.display_name = "Test User"
    message.author.bot = False

    message.content = "원본 메시지"
    message.attachments = []
    message.reference = None
    message.created_at = datetime(2026, 8, 18, tzinfo=timezone.utc)
    message.edited_at = None

    return message


def test_collector_collects_guild_message_without_analysis_channel_filter():
    service = Mock()

    with patch(
        "app.collectors.message_collector.MessageService",
        return_value=service,
    ):
        collector = MessageCollector()

    message = create_guild_message()

    asyncio.run(collector.collect(message))

    service.save.assert_called_once()

    saved_dto = service.save.call_args.args[0]

    assert saved_dto.guild_id == 100
    assert saved_dto.channel_id == 200
    assert saved_dto.channel_name == "비활성-분석-채널"
