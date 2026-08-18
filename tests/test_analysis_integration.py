from datetime import datetime, timezone

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.collection_channel import CollectionChannel
from app.models.message import Message
from app.repositories import collection_channel_repository
from app.repositories import message_repository
from app.services.analysis_service import AnalysisService
from app.dto.analysis_request_dto import AnalysisRequestDTO


@pytest.fixture
def test_session_local(monkeypatch):
    """
    테스트 전용 SQLite 메모리 DB를 생성한다.
    실제 Chronicle DB에는 영향을 주지 않는다.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(
        collection_channel_repository,
        "SessionLocal",
        TestSessionLocal,
    )

    monkeypatch.setattr(
        message_repository,
        "SessionLocal",
        TestSessionLocal,
    )

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_channel(
    *,
    guild_id: int,
    channel_id: int,
    channel_name: str,
    enabled: bool,
) -> CollectionChannel:

    return CollectionChannel(
        guild_id=guild_id,
        channel_id=channel_id,
        channel_name=channel_name,
        enabled=enabled,
    )


def create_message(
    *,
    discord_message_id: int,
    guild_id: int,
    channel_id: int,
    channel_name: str,
    author_id: int,
    author_display_name: str,
    content: str,
    created_at: datetime,
) -> Message:

    return Message(
        discord_message_id=discord_message_id,

        guild_id=guild_id,
        guild_name="Test Guild",

        channel_id=channel_id,
        channel_name=channel_name,

        author_id=author_id,
        author_username=f"user-{author_id}",
        author_display_name=author_display_name,

        is_bot=False,

        content=content,
        language="ko",

        has_attachment=False,
        attachment_count=0,

        reply_to_message_id=None,

        created_at=created_at,
        edited_at=None,
    )


def test_analysis_service_analyzes_real_test_database(
    test_session_local,
):
    base_time = datetime(
        2026,
        8,
        1,
        10,
        tzinfo=timezone.utc,
    )

    with test_session_local() as session:

        session.add_all(
            [
                create_channel(
                    guild_id=100,
                    channel_id=10,
                    channel_name="일반",
                    enabled=True,
                ),
                create_channel(
                    guild_id=100,
                    channel_id=20,
                    channel_name="잡담",
                    enabled=True,
                ),
                create_channel(
                    guild_id=100,
                    channel_id=30,
                    channel_name="공지",
                    enabled=False,
                ),
            ]
        )

        session.add_all(
            [
                create_message(
                    discord_message_id=1,
                    guild_id=100,
                    channel_id=10,
                    channel_name="일반",
                    author_id=1,
                    author_display_name="M.K",
                    content="첫 번째 메시지",
                    created_at=base_time,
                ),
                create_message(
                    discord_message_id=2,
                    guild_id=100,
                    channel_id=10,
                    channel_name="일반",
                    author_id=1,
                    author_display_name="M.K",
                    content="두 번째 메시지",
                    created_at=base_time.replace(
                        hour=11,
                    ),
                ),
                create_message(
                    discord_message_id=3,
                    guild_id=100,
                    channel_id=20,
                    channel_name="잡담",
                    author_id=2,
                    author_display_name="S.M☆",
                    content="세 번째 메시지",
                    created_at=base_time.replace(
                        hour=12,
                    ),
                ),
                create_message(
                    discord_message_id=4,
                    guild_id=100,
                    channel_id=20,
                    channel_name="잡담",
                    author_id=2,
                    author_display_name="S.M☆",
                    content="네 번째 메시지",
                    created_at=base_time.replace(
                        hour=13,
                    ),
                ),
                create_message(
                    discord_message_id=5,
                    guild_id=100,
                    channel_id=30,
                    channel_name="공지",
                    author_id=1,
                    author_display_name="M.K",
                    content="비활성 채널 메시지",
                    created_at=base_time.replace(
                        hour=14,
                    ),
                ),
            ]
        )

        session.commit()

    service = AnalysisService()

    request = AnalysisRequestDTO(
        guild_id=100,
        start_at=datetime(
            2026,
            8,
            1,
            0,
            tzinfo=timezone.utc,
        ),
        end_at=datetime(
            2026,
            8,
            2,
            0,
            tzinfo=timezone.utc,
        ),
        output_language="ko",
    )

    result = service.analyze(request)

    assert result.message_count == 4
    assert result.author_count == 2
    assert result.channel_count == 2

    assert result.language_distribution == {
        "ko": 1.0,
    }

    assert [
        (
            author.author_display_name,
            author.message_count,
        )
        for author in result.top_authors
    ] == [
        ("M.K", 2),
        ("S.M☆", 2),
    ]

    assert [
        (
            channel.channel_name,
            channel.message_count,
        )
        for channel in result.channel_activity
    ] == [
        ("일반", 2),
        ("잡담", 2),
    ]

    assert [
        (
            activity.date,
            activity.message_count,
        )
        for activity in result.daily_activity
    ] == [
        (
            "2026-08-01",
            4,
        ),
    ]

    assert [
        (
            activity.date,
            activity.message_count,
        )
        for activity in result.daily_activity
    ] == [
        (
            "2026-08-01",
            4,
        ),
    ]

    assert [
        (
            activity.hour,
            activity.message_count,
        )
        for activity in result.hourly_activity
    ] == [
        (
            10,
            1,
        ),
        (
            11,
            1,
        ),
        (
            12,
            1,
        ),
        (
            13,
            1,
        ),
    ]