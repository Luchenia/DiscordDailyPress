from datetime import UTC
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.message import Message
from app.models.message_translation import MessageTranslation
from app.repositories import message_translation_repository
from app.repositories.message_translation_repository import (
    MessageTranslationRepository,
)
from app.utils.content_hash import calculate_source_content_hash
from app.utils.datetime_utils import ensure_utc


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
    monkeypatch.setattr(
        message_translation_repository,
        "SessionLocal",
        TestSessionLocal,
    )

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def save_message(
    session_local,
    *,
    discord_message_id: int,
    content: str,
    language: str,
) -> int:
    message = Message(
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
        language=language,
        has_attachment=False,
        attachment_count=0,
        reply_to_message_id=None,
        created_at=datetime.now(UTC),
        edited_at=None,
    )

    with session_local() as session:
        session.add(message)
        session.commit()
        session.refresh(message)

        return message.id


def create_translation(
    *,
    message_id: int,
    source_language: str,
    target_language: str,
    source_content: str,
    translated_content: str,
) -> MessageTranslation:
    return MessageTranslation(
        message_id=message_id,
        source_language=source_language,
        target_language=target_language,
        source_content_hash=calculate_source_content_hash(source_content),
        translated_content=translated_content,
    )


def test_translation_is_stored_without_changing_raw_message(
    test_session_local,
):
    message_id = save_message(
        test_session_local,
        discord_message_id=1001,
        content="hello",
        language="en",
    )
    repository = MessageTranslationRepository()
    source_hash = calculate_source_content_hash("hello")

    saved = repository.save(
        create_translation(
            message_id=message_id,
            source_language="en",
            target_language="ko",
            source_content="hello",
            translated_content="안녕하세요",
        )
    )

    with test_session_local() as session:
        message = session.get(Message, message_id)

    assert message is not None
    assert message.content == "hello"
    assert message.language == "en"
    assert saved.source_language == "en"
    assert saved.target_language == "ko"
    assert saved.source_content_hash == source_hash
    assert ensure_utc(saved.created_at).tzinfo is UTC
    assert repository.get_current(message_id, "ko").id == saved.id
    assert source_hash == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e"
        "1b161e5c1fa7425e73043362938b9824"
    )


def test_translation_uniqueness_allows_other_targets_and_messages(
    test_session_local,
):
    first_message_id = save_message(
        test_session_local,
        discord_message_id=1001,
        content="hello",
        language="en",
    )
    second_message_id = save_message(
        test_session_local,
        discord_message_id=1002,
        content="hello",
        language="en",
    )
    repository = MessageTranslationRepository()

    repository.save(
        create_translation(
            message_id=first_message_id,
            source_language="en",
            target_language="ko",
            source_content="hello",
            translated_content="안녕하세요",
        )
    )

    with pytest.raises(IntegrityError):
        repository.save(
            create_translation(
                message_id=first_message_id,
                source_language="en",
                target_language="ko",
                source_content="hello",
                translated_content="중복 번역",
            )
        )

    repository.save(
        create_translation(
            message_id=first_message_id,
            source_language="en",
            target_language="ja",
            source_content="hello",
            translated_content="こんにちは",
        )
    )
    repository.save(
        create_translation(
            message_id=second_message_id,
            source_language="en",
            target_language="ko",
            source_content="hello",
            translated_content="두 번째 메시지 번역",
        )
    )

    with test_session_local() as session:
        translation_count = session.scalar(
            select(func.count()).select_from(MessageTranslation)
        )

    assert translation_count == 3


def test_current_lookup_ignores_stale_translation_after_message_edit(
    test_session_local,
):
    message_id = save_message(
        test_session_local,
        discord_message_id=1001,
        content="hello",
        language="en",
    )
    repository = MessageTranslationRepository()
    old_hash = calculate_source_content_hash("hello")
    old_translation = repository.save(
        create_translation(
            message_id=message_id,
            source_language="en",
            target_language="ko",
            source_content="hello",
            translated_content="안녕하세요",
        )
    )

    with test_session_local() as session:
        message = session.get(Message, message_id)
        assert message is not None
        message.content = "hello world"
        session.commit()

    new_hash = calculate_source_content_hash("hello world")

    assert old_hash != new_hash
    assert repository.get_current(message_id, "ko") is None
    assert repository.get_by_source_content_hash(
        message_id,
        "ko",
        old_hash,
    ).id == old_translation.id

    new_translation = repository.save(
        create_translation(
            message_id=message_id,
            source_language="en",
            target_language="ko",
            source_content="hello world",
            translated_content="안녕하세요, 세상",
        )
    )

    current = repository.get_current(message_id, "ko")

    assert current is not None
    assert current.id == new_translation.id

    with test_session_local() as session:
        translations = list(
            session.scalars(
                select(MessageTranslation).where(
                    MessageTranslation.message_id == message_id
                )
            )
        )

    assert len(translations) == 2
    assert {item.source_content_hash for item in translations} == {
        old_hash,
        new_hash,
    }
