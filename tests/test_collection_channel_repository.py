import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.models.collection_channel import CollectionChannel
from app.repositories import collection_channel_repository
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)


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

    yield TestSessionLocal

    Base.metadata.drop_all(bind=engine)


def create_channel(
    guild_id: int = 100,
    channel_id: int = 200,
    channel_name: str = "일반",
    enabled: bool = True,
) -> CollectionChannel:

    return CollectionChannel(
        guild_id=guild_id,
        channel_id=channel_id,
        channel_name=channel_name,
        enabled=enabled,
    )


def test_repository_add_and_get_by_guild(
    test_session_local,
):
    repository = CollectionChannelRepository()

    channel = create_channel()

    saved = repository.add(channel)

    assert saved.id is not None
    assert saved.guild_id == 100
    assert saved.channel_id == 200
    assert saved.channel_name == "일반"
    assert saved.enabled is True

    channels = repository.get_by_guild(100)

    assert len(channels) == 1
    assert channels[0].channel_id == 200


def test_repository_get_enabled_channel_ids(
    test_session_local,
):
    repository = CollectionChannelRepository()

    repository.add(
        create_channel(
            channel_id=200,
            channel_name="일반",
            enabled=True,
        )
    )

    repository.add(
        create_channel(
            channel_id=300,
            channel_name="공지",
            enabled=False,
        )
    )

    repository.add(
        create_channel(
            channel_id=400,
            channel_name="잡담",
            enabled=True,
        )
    )

    channel_ids = repository.get_enabled_channel_ids(100)

    assert channel_ids == [200, 400]


def test_repository_disable(
    test_session_local,
):
    repository = CollectionChannelRepository()

    channel = repository.add(
        create_channel()
    )

    success = repository.disable(
        guild_id=100,
        channel_id=200,
    )

    assert success is True

    channels = repository.get_by_guild(100)

    assert len(channels) == 1
    assert channels[0].id == channel.id
    assert channels[0].enabled is False


def test_repository_disable_returns_false_when_not_found(
    test_session_local,
):
    repository = CollectionChannelRepository()

    success = repository.disable(
        guild_id=100,
        channel_id=999,
    )

    assert success is False

def test_repository_enable(
    test_session_local,
):

    repository = CollectionChannelRepository()

    channel = repository.add(
        create_channel()
    )

    repository.disable(
        guild_id=100,
        channel_id=200,
    )

    success = repository.enable(
        guild_id=100,
        channel_id=200,
    )

    assert success is True

    channels = repository.get_by_guild(100)

    assert len(channels) == 1
    assert channels[0].id == channel.id
    assert channels[0].enabled is True


def test_repository_enable_returns_false_when_not_found(
    test_session_local,
):

    repository = CollectionChannelRepository()

    success = repository.enable(
        guild_id=100,
        channel_id=999,
    )

    assert success is False