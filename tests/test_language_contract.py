from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.discord_message_dto import DiscordMessageDTO
from app.models.collection_channel import CollectionChannel
from app.models.message import Message
from app.repositories import collection_channel_repository
from app.repositories import message_repository
from app.services import message_service
from app.services.analysis_service import AnalysisService
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
        collection_channel_repository,
        "SessionLocal",
        TestSessionLocal,
    )
    monkeypatch.setattr(message_service, "SessionLocal", TestSessionLocal)

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_dto(
    discord_message_id: int,
    content: str,
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
        edited_at=None,
    )


def test_flush_stores_source_languages_and_analysis_ignores_output_language(
    test_session_local,
    monkeypatch,
):
    service = MessageService()
    english = service.save(create_dto(1001, "Hello everyone"))
    korean = service.save(create_dto(1002, "안녕하세요"))

    assert english is not None
    assert korean is not None

    monkeypatch.setattr(
        service.conversation_buffer.language_service,
        "detect",
        lambda text: "mixed",
    )
    monkeypatch.setattr(
        service.language_service,
        "detect",
        lambda text: {
            "Hello everyone": "en",
            "안녕하세요": "ko",
        }[text],
    )

    results = service.conversation_buffer.flush_all()

    assert len(results) == 1
    assert results[0].language == "mixed"

    with test_session_local() as session:
        session.add(
            CollectionChannel(
                guild_id=100,
                channel_id=200,
                channel_name="general",
                enabled=True,
            )
        )
        session.commit()

    request = AnalysisRequestDTO(
        guild_id=100,
        start_at=datetime.now(UTC) - timedelta(days=1),
        end_at=datetime.now(UTC) + timedelta(days=1),
        output_language="ja",
    )
    statistics = AnalysisService().analyze(request)

    with test_session_local() as session:
        stored_languages = {
            message.discord_message_id: message.language
            for message in session.scalars(select(Message))
        }

    assert stored_languages == {1001: "en", 1002: "ko"}
    assert statistics.language_distribution == {"en": 0.5, "ko": 0.5}
