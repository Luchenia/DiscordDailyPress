from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.models.message import Message
from app.services.analysis_service import AnalysisService
from app.dto.analysis_message_dto import AnalysisMessageDTO


def create_message(
    discord_message_id: int,
    guild_id: int,
    channel_id: int,
    content: str,
    created_at: datetime,
) -> Message:

    return Message(
        discord_message_id=discord_message_id,

        guild_id=guild_id,
        guild_name="Test Guild",

        channel_id=channel_id,
        channel_name=f"channel-{channel_id}",

        author_id=1,
        author_username="test_user",
        author_display_name="Test User",

        is_bot=False,

        content=content,
        language="ko",

        has_attachment=False,
        attachment_count=0,

        reply_to_message_id=None,

        created_at=created_at,
        edited_at=None,
    )


def test_get_messages_returns_repository_results():
    service = AnalysisService()

    mock_repository = Mock()
    service.repository = mock_repository

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=1,
            guild_id=100,
            channel_id=10,
            content="첫 번째 메시지",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=2,
            guild_id=100,
            channel_id=20,
            content="두 번째 메시지",
            created_at=base_time + timedelta(minutes=1),
        ),
    ]

    mock_repository.get_by_analysis_scope.return_value = messages

    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=base_time,
        end_at=base_time + timedelta(hours=1),
    )

    result = service.get_messages(scope)

    assert result == messages

def test_get_messages_passes_scope_to_repository():
    service = AnalysisService()

    mock_repository = Mock()
    service.repository = mock_repository

    mock_repository.get_by_analysis_scope.return_value = []

    base_time = datetime.now(timezone.utc)

    scope = AnalysisScopeDTO(
        guild_id=123,
        channel_ids=[10, 20, 30],
        start_at=base_time,
        end_at=base_time + timedelta(days=1),
    )

    service.get_messages(scope)

    mock_repository.get_by_analysis_scope.assert_called_once_with(
        guild_id=123,
        channel_ids=[10, 20, 30],
        start_at=base_time,
        end_at=base_time + timedelta(days=1),
    )



def test_to_analysis_message_converts_message():
    service = AnalysisService()

    created_at = datetime.now(timezone.utc)

    message = create_message(
        discord_message_id=100,
        guild_id=200,
        channel_id=300,
        content="테스트 메시지",
        created_at=created_at,
    )

    result = service.to_analysis_message(message)

    assert isinstance(result, AnalysisMessageDTO)

    assert result.message_id == 100
    assert result.guild_id == 200
    assert result.channel_id == 300
    assert result.channel_name == "channel-300"

    assert result.author_id == 1
    assert result.author_display_name == "Test User"

    assert result.content == "테스트 메시지"
    assert result.language == "ko"
    assert result.created_at == created_at



def test_to_analysis_message_does_not_modify_original_message():
    service = AnalysisService()

    created_at = datetime.now(timezone.utc)

    message = create_message(
        discord_message_id=101,
        guild_id=200,
        channel_id=300,
        content="원본 메시지",
        created_at=created_at,
    )

    original_content = message.content
    original_language = message.language

    result = service.to_analysis_message(message)

    result.content = "변경된 분석 데이터"
    result.language = "en"

    assert message.content == original_content
    assert message.language == original_language



def test_build_dataset_creates_dataset_with_metadata():
    service = AnalysisService()

    mock_repository = Mock()
    service.repository = mock_repository

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=200,
            guild_id=100,
            channel_id=10,
            content="한국어 메시지 1",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=201,
            guild_id=100,
            channel_id=10,
            content="한국어 메시지 2",
            created_at=base_time + timedelta(minutes=1),
        ),
        create_message(
            discord_message_id=202,
            guild_id=100,
            channel_id=20,
            content="영어 메시지",
            created_at=base_time + timedelta(minutes=2),
        ),
        create_message(
            discord_message_id=203,
            guild_id=100,
            channel_id=20,
            content="한국어 메시지 3",
            created_at=base_time + timedelta(minutes=3),
        ),
    ]

    messages[0].language = "ko"
    messages[1].language = "ko"
    messages[2].language = "en"
    messages[3].language = "ko"

    mock_repository.get_by_analysis_scope.return_value = messages

    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=base_time,
        end_at=base_time + timedelta(hours=1),
    )

    dataset = service.build_dataset(scope)

    assert dataset.scope == scope

    assert len(dataset.messages) == 4

    assert dataset.metadata.message_count == 4
    assert dataset.metadata.author_count == 1
    assert dataset.metadata.channel_count == 2

    assert dataset.metadata.language_distribution == {
        "ko": 0.75,
        "en": 0.25,
    }

def test_build_dataset_handles_empty_result():
    service = AnalysisService()

    mock_repository = Mock()
    service.repository = mock_repository

    mock_repository.get_by_analysis_scope.return_value = []

    base_time = datetime.now(timezone.utc)

    scope = AnalysisScopeDTO(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=base_time,
        end_at=base_time + timedelta(hours=1),
    )

    dataset = service.build_dataset(scope)

    assert dataset.scope == scope

    assert dataset.messages == []

    assert dataset.metadata.message_count == 0
    assert dataset.metadata.author_count == 0
    assert dataset.metadata.channel_count == 0
    assert dataset.metadata.language_distribution == {}