from datetime import datetime, timedelta, timezone

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.message import Message
from app.repositories import message_repository
from app.repositories.message_repository import MessageRepository


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
        message_repository,
        "SessionLocal",
        TestSessionLocal,
    )

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_message(
    *,
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
        language="unknown",

        has_attachment=False,
        attachment_count=0,

        reply_to_message_id=None,

        created_at=created_at,
        edited_at=None,
    )


def test_get_by_analysis_scope_returns_matching_messages(
    test_session_local,
):
    repository = MessageRepository()

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=1,
            guild_id=100,
            channel_id=10,
            content="일반 채널 메시지",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=2,
            guild_id=100,
            channel_id=20,
            content="잡담 채널 메시지",
            created_at=base_time + timedelta(minutes=1),
        ),
        create_message(
            discord_message_id=3,
            guild_id=100,
            channel_id=30,
            content="다른 채널 메시지",
            created_at=base_time + timedelta(minutes=2),
        ),
        create_message(
            discord_message_id=4,
            guild_id=200,
            channel_id=10,
            content="다른 길드 메시지",
            created_at=base_time + timedelta(minutes=3),
        ),
        create_message(
            discord_message_id=5,
            guild_id=100,
            channel_id=10,
            content="기간 밖 메시지",
            created_at=base_time - timedelta(days=1),
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    result_ids = [
        message.discord_message_id
        for message in results
    ]

    assert result_ids == [1, 2]


def test_get_by_analysis_scope_excludes_other_guild(
    test_session_local,
):
    repository = MessageRepository()

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=10,
            guild_id=100,
            channel_id=10,
            content="Guild 100",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=11,
            guild_id=200,
            channel_id=10,
            content="Guild 200",
            created_at=base_time,
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    assert len(results) == 1
    assert results[0].discord_message_id == 10


def test_get_by_analysis_scope_excludes_other_channels(
    test_session_local,
):
    repository = MessageRepository()

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=20,
            guild_id=100,
            channel_id=10,
            content="포함",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=21,
            guild_id=100,
            channel_id=20,
            content="제외",
            created_at=base_time,
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    assert len(results) == 1
    assert results[0].discord_message_id == 20


def test_get_by_analysis_scope_excludes_messages_outside_period(
    test_session_local,
):
    repository = MessageRepository()

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=30,
            guild_id=100,
            channel_id=10,
            content="기간 이전",
            created_at=base_time - timedelta(seconds=1),
        ),
        create_message(
            discord_message_id=31,
            guild_id=100,
            channel_id=10,
            content="기간 시작",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=32,
            guild_id=100,
            channel_id=10,
            content="기간 내부",
            created_at=base_time + timedelta(minutes=1),
        ),
        create_message(
            discord_message_id=33,
            guild_id=100,
            channel_id=10,
            content="기간 종료",
            created_at=base_time + timedelta(hours=1),
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10],
        start_at=base_time,
        end_at=base_time + timedelta(hours=1),
    )

    result_ids = [
        message.discord_message_id
        for message in results
    ]

    assert result_ids == [31, 32]


def test_get_by_analysis_scope_supports_multiple_channels(
    test_session_local,
):
    repository = MessageRepository()

    base_time = datetime.now(timezone.utc)

    messages = [
        create_message(
            discord_message_id=40,
            guild_id=100,
            channel_id=10,
            content="채널 10",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=41,
            guild_id=100,
            channel_id=20,
            content="채널 20",
            created_at=base_time + timedelta(minutes=1),
        ),
        create_message(
            discord_message_id=42,
            guild_id=100,
            channel_id=30,
            content="채널 30",
            created_at=base_time + timedelta(minutes=2),
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10, 20],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    result_ids = [
        message.discord_message_id
        for message in results
    ]

    assert result_ids == [40, 41]


def test_get_by_analysis_scope_orders_by_created_at_then_message_identity(
    test_session_local,
):
    repository = MessageRepository()
    base_time = datetime.now(timezone.utc)
    messages = [
        create_message(
            discord_message_id=73,
            guild_id=100,
            channel_id=10,
            content="나중 메시지",
            created_at=base_time + timedelta(minutes=1),
        ),
        create_message(
            discord_message_id=72,
            guild_id=100,
            channel_id=10,
            content="같은 시간 높은 ID",
            created_at=base_time,
        ),
        create_message(
            discord_message_id=71,
            guild_id=100,
            channel_id=10,
            content="같은 시간 낮은 ID",
            created_at=base_time,
        ),
    ]

    with test_session_local() as session:
        session.add_all(messages)
        session.commit()

    results = repository.get_by_analysis_scope(
        guild_id=100,
        channel_ids=[10],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    assert [message.discord_message_id for message in results] == [71, 72, 73]
