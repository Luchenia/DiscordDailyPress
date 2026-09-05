from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.message import Message
from app.models.message_delete_history import MessageDeleteHistory
from app.repositories import message_delete_history_repository
from app.repositories import message_repository
from app.repositories.message_repository import MessageRepository
from app.services import message_service
from app.services.message_service import MessageService


@pytest.fixture
def test_session_local(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    TestSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(message_repository, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(
        message_delete_history_repository,
        "SessionLocal",
        TestSessionLocal,
    )
    monkeypatch.setattr(message_service, "SessionLocal", TestSessionLocal)

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_message(created_at: datetime) -> Message:
    return Message(
        discord_message_id=1001,
        guild_id=100,
        guild_name="Test Guild",
        channel_id=200,
        channel_name="general",
        author_id=300,
        author_username="test-user",
        author_display_name="Test User",
        is_bot=False,
        content="original raw content",
        language="unknown",
        has_attachment=False,
        attachment_count=0,
        reply_to_message_id=None,
        created_at=created_at,
        edited_at=None,
    )


def test_delete_soft_deletes_message_preserves_raw_data_and_is_idempotent(
    test_session_local,
):
    created_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with test_session_local() as session:
        session.add(create_message(created_at))
        session.commit()

    service = MessageService()

    assert service.delete(1001) is True

    with test_session_local() as session:
        message = session.scalar(
            select(Message).where(Message.discord_message_id == 1001)
        )
        histories = list(session.scalars(select(MessageDeleteHistory)))

        assert message is not None
        assert message.content == "original raw content"
        assert message.deleted_at is not None
        assert len(histories) == 1
        assert histories[0].message_id == message.id
        assert histories[0].content == "original raw content"
        deleted_at = message.deleted_at

    assert service.delete(1001) is True

    with test_session_local() as session:
        message = session.scalar(
            select(Message).where(Message.discord_message_id == 1001)
        )
        histories = list(session.scalars(select(MessageDeleteHistory)))

        assert message is not None
        assert message.content == "original raw content"
        assert message.deleted_at == deleted_at
        assert len(histories) == 1


def test_analysis_scope_excludes_soft_deleted_messages(test_session_local):
    base_time = datetime.now(timezone.utc)

    active_message = create_message(base_time)
    active_message.discord_message_id = 1002
    deleted_message = create_message(base_time)
    deleted_message.discord_message_id = 1003
    deleted_message.deleted_at = base_time

    with test_session_local() as session:
        session.add_all([active_message, deleted_message])
        session.commit()

    messages = MessageRepository().get_by_analysis_scope(
        guild_id=100,
        channel_ids=[200],
        start_at=base_time - timedelta(hours=1),
        end_at=base_time + timedelta(hours=1),
    )

    assert [message.discord_message_id for message in messages] == [1002]


def test_delete_rolls_back_history_when_soft_delete_fails(
    test_session_local,
    monkeypatch,
):
    created_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    with test_session_local() as session:
        session.add(create_message(created_at))
        session.commit()

    service = MessageService()

    def fail_soft_delete(*args, **kwargs):
        raise RuntimeError("forced soft delete failure")

    monkeypatch.setattr(
        service.repository,
        "soft_delete_by_id",
        fail_soft_delete,
    )

    with pytest.raises(RuntimeError, match="forced soft delete failure"):
        service.delete(1001)

    with test_session_local() as session:
        message = session.scalar(
            select(Message).where(Message.discord_message_id == 1001)
        )
        histories = list(session.scalars(select(MessageDeleteHistory)))

        assert message is not None
        assert message.content == "original raw content"
        assert message.deleted_at is None
        assert histories == []
