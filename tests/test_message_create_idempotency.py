from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dto.discord_message_dto import DiscordMessageDTO
from app.models.message import Message
from app.models.message_history import MessageHistory
from app.repositories import message_history_repository
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
        message_history_repository,
        "SessionLocal",
        TestSessionLocal,
    )
    monkeypatch.setattr(message_service, "SessionLocal", TestSessionLocal)

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_dto(
    discord_message_id: int,
    content: str,
    *,
    edited_at: datetime | None = None,
) -> DiscordMessageDTO:
    return DiscordMessageDTO(
        discord_message_id=discord_message_id,
        guild_id=100,
        guild_name="Test Guild",
        channel_id=200,
        channel_name="general",
        author_id=300,
        author_username="test-user",
        author_display_name="Test User",
        is_bot=False,
        content=content,
        has_attachment=False,
        attachment_count=0,
        reply_to_message_id=None,
        created_at=datetime.now(UTC),
        edited_at=edited_at,
    )


def create_message(discord_message_id: int, content: str) -> Message:
    dto = create_dto(discord_message_id, content)

    return Message(
        discord_message_id=dto.discord_message_id,
        guild_id=dto.guild_id,
        guild_name=dto.guild_name,
        channel_id=dto.channel_id,
        channel_name=dto.channel_name,
        author_id=dto.author_id,
        author_username=dto.author_username,
        author_display_name=dto.author_display_name,
        is_bot=dto.is_bot,
        content=dto.content,
        language="unknown",
        has_attachment=dto.has_attachment,
        attachment_count=dto.attachment_count,
        reply_to_message_id=dto.reply_to_message_id,
        created_at=dto.created_at,
        edited_at=dto.edited_at,
    )


def test_duplicate_create_preserves_row_content_and_conversation_buffer(
    test_session_local,
):
    service = MessageService()
    first_dto = create_dto(1001, "original content")
    duplicate_dto = create_dto(1001, "incoming duplicate content")

    first = service.save(first_dto)
    duplicate = service.save(duplicate_dto)

    assert first is not None
    assert first.created is True
    assert duplicate is not None
    assert duplicate.created is False
    assert duplicate.message.id == first.message.id
    assert duplicate.message.content == "original content"

    with test_session_local() as session:
        messages = list(session.scalars(select(Message)))

    assert len(messages) == 1
    assert messages[0].content == "original content"

    conversation = service.conversation_buffer.sessions[(300, 200)]
    assert [message.discord_message_id for message in conversation.messages] == [
        1001
    ]


def test_repository_recovers_from_duplicate_integrity_error_and_can_save_again(
    test_session_local,
):
    repository = MessageRepository()

    first = repository.save(create_message(1001, "original content"))
    duplicate = repository.save(create_message(1001, "duplicate content"))
    following = repository.save(create_message(1002, "following content"))

    assert first.created is True
    assert duplicate.created is False
    assert duplicate.message.id == first.message.id
    assert duplicate.message.content == "original content"
    assert following.created is True

    with test_session_local() as session:
        assert session.query(Message).count() == 2


def test_edit_flow_still_updates_content_after_create(test_session_local):
    service = MessageService()
    created = service.save(create_dto(1001, "original content"))

    updated = service.update(
        create_dto(
            1001,
            "edited content",
            edited_at=datetime.now(UTC) + timedelta(seconds=1),
        )
    )

    assert created is not None
    assert created.created is True
    assert updated is not None
    assert updated.content == "edited content"

    with test_session_local() as session:
        stored = session.scalar(
            select(Message).where(Message.discord_message_id == 1001)
        )

    assert stored is not None
    assert stored.content == "edited content"


def test_message_history_versions_and_content_are_per_message(
    test_session_local,
):
    service = MessageService()
    first = service.save(create_dto(1001, "original"))
    second = service.save(create_dto(1002, "other original"))

    assert first is not None
    assert second is not None

    for content in ("first edit", "second edit", "third edit"):
        service.update(
            create_dto(
                1001,
                content,
                edited_at=datetime.now(UTC),
            )
        )

    service.update(
        create_dto(
            1002,
            "other edit",
            edited_at=datetime.now(UTC),
        )
    )

    with test_session_local() as session:
        first_histories = list(
            session.scalars(
                select(MessageHistory)
                .where(MessageHistory.message_id == first.message.id)
                .order_by(MessageHistory.version)
            )
        )
        second_histories = list(
            session.scalars(
                select(MessageHistory)
                .where(MessageHistory.message_id == second.message.id)
                .order_by(MessageHistory.version)
            )
        )
        first_message = session.get(Message, first.message.id)
        second_message = session.get(Message, second.message.id)

    assert [history.version for history in first_histories] == [1, 2, 3]
    assert [
        (history.old_content, history.new_content)
        for history in first_histories
    ] == [
        ("original", "first edit"),
        ("first edit", "second edit"),
        ("second edit", "third edit"),
    ]
    assert [history.version for history in second_histories] == [1]
    assert [
        (history.old_content, history.new_content)
        for history in second_histories
    ] == [("other original", "other edit")]
    assert first_message is not None
    assert first_message.content == "third edit"
    assert second_message is not None
    assert second_message.content == "other edit"
