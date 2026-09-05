import asyncio
from datetime import datetime, timedelta, timezone

from app.dto.discord_message_dto import DiscordMessageDTO
from app.services.conversation_buffer import ConversationBuffer


def create_message(
    author_id: int,
    channel_id: int,
    content: str,
    created_at: datetime,
) -> DiscordMessageDTO:

    return DiscordMessageDTO(
        discord_message_id=1,
        guild_id=100,
        guild_name="Test Guild",

        channel_id=channel_id,
        channel_name="general",

        author_id=author_id,
        author_username="test_user",
        author_display_name="Test User",

        is_bot=False,

        content=content,

        has_attachment=False,
        attachment_count=0,

        reply_to_message_id=None,

        created_at=created_at,
        edited_at=None,
    )


def test_messages_within_5_seconds_share_session():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=1,
        channel_id=100,
        content="녕",
        created_at=base_time + timedelta(seconds=2),
    )

    session1 = buffer.add(message1)
    session2 = buffer.add(message2)

    assert session1 is session2
    assert len(session1.messages) == 2


def test_messages_after_5_seconds_create_new_session():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안녕하세요",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=1,
        channel_id=100,
        content="오늘 뭐해?",
        created_at=base_time + timedelta(seconds=6),
    )

    session1 = buffer.add(message1)
    session2 = buffer.add(message2)

    assert session1 is not session2

    assert len(session1.messages) == 1
    assert len(session2.messages) == 1


def test_expired_session_is_flushed_before_new_message_starts_session():
    flushed = []
    buffer = ConversationBuffer(result_handler=flushed.append)
    base_time = datetime.now(timezone.utc)

    expired_message = create_message(
        author_id=1,
        channel_id=100,
        content="expired",
        created_at=base_time,
    )
    new_message = create_message(
        author_id=1,
        channel_id=100,
        content="new",
        created_at=base_time + timedelta(seconds=6),
    )

    old_session = buffer.add(expired_message)
    new_session = buffer.add(new_message)

    assert [result.text for result in flushed] == ["expired"]
    assert old_session is not new_session
    assert new_session.messages == [new_message]
    assert buffer.sessions[(1, 100)] is new_session


def test_different_channels_create_different_sessions():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안녕",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=1,
        channel_id=200,
        content="다른 채널",
        created_at=base_time + timedelta(seconds=1),
    )

    session1 = buffer.add(message1)
    session2 = buffer.add(message2)

    assert session1 is not session2


def test_different_users_create_different_sessions():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안녕",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=2,
        channel_id=100,
        content="뭐해?",
        created_at=base_time + timedelta(seconds=1),
    )

    session1 = buffer.add(message1)
    session2 = buffer.add(message2)

    assert session1 is not session2


def test_expired_session_is_flushed():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message = create_message(
        author_id=1,
        channel_id=100,
        content="안녕하세요",
        created_at=base_time,
    )

    session = buffer.add(message)

    # 세션의 마지막 메시지 시간을 6초 전으로 변경
    session.last_message_at = (
        base_time - timedelta(seconds=6)
    )

    results = buffer.flush_expired()

    assert len(results) == 1

    result = results[0]

    assert result.author_id == 1
    assert result.channel_id == 100
    assert result.text == "안녕하세요"
    assert result.language == "ko"
    assert result.message_ids == [
        message.discord_message_id
    ]

    assert result.started_at == session.started_at
    assert result.ended_at == session.last_message_at

    assert len(buffer.sessions) == 0

def test_conversation_result_contains_all_message_ids():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=1,
        channel_id=100,
        content="녕",
        created_at=base_time + timedelta(seconds=1),
    )

    message3 = create_message(
        author_id=1,
        channel_id=100,
        content="하세요",
        created_at=base_time + timedelta(seconds=2),
    )

    buffer.add(message1)
    buffer.add(message2)
    session = buffer.add(message3)

    session.last_message_at = (
        base_time - timedelta(seconds=6)
    )

    results = buffer.flush_expired()

    assert len(results) == 1

    result = results[0]

    assert result.message_ids == [
        message1.discord_message_id,
        message2.discord_message_id,
        message3.discord_message_id,
    ]


def test_flush_all_flushes_each_remaining_session_once():
    flushed = []
    buffer = ConversationBuffer(result_handler=flushed.append)
    base_time = datetime.now(timezone.utc)

    buffer.add(create_message(1, 100, "one", base_time))
    buffer.add(create_message(2, 100, "two", base_time))

    results = buffer.flush_all()

    assert {result.text for result in results} == {"one", "two"}
    assert len(flushed) == 2
    assert buffer.sessions == {}
    assert buffer.flush_all() == []
    assert len(flushed) == 2


def test_stop_cleanup_cancels_task_and_flushes_remaining_sessions():
    async def run_test():
        flushed = []
        buffer = ConversationBuffer(result_handler=flushed.append)
        buffer.add(
            create_message(
                1,
                100,
                "shutdown",
                datetime.now(timezone.utc),
            )
        )
        buffer.start_cleanup()
        task = buffer._cleanup_task

        results = await buffer.stop_cleanup()

        assert [result.text for result in results] == ["shutdown"]
        assert [result.text for result in flushed] == ["shutdown"]
        assert task is not None
        assert task.done()
        assert buffer._cleanup_task is None
        assert buffer.sessions == {}

    asyncio.run(run_test())


def test_stop_cleanup_flushes_when_done_task_failed_unexpectedly():
    async def run_test():
        flushed = []
        buffer = ConversationBuffer(result_handler=flushed.append)
        buffer.add(
            create_message(
                1,
                100,
                "after-task-failure",
                datetime.now(timezone.utc),
            )
        )

        async def fail_cleanup():
            raise RuntimeError("forced cleanup task failure")

        buffer._cleanup_task = asyncio.create_task(fail_cleanup())
        await asyncio.sleep(0)

        results = await buffer.stop_cleanup()

        assert [result.text for result in results] == [
            "after-task-failure"
        ]
        assert [result.text for result in flushed] == [
            "after-task-failure"
        ]
        assert buffer.sessions == {}

    asyncio.run(run_test())


def test_cleanup_retries_failed_session_and_continues_other_sessions():
    async def run_test():
        calls = []
        failed_once = False

        def handler(result):
            nonlocal failed_once
            calls.append(result.text)

            if result.text == "fail" and not failed_once:
                failed_once = True
                raise RuntimeError("forced handler failure")

        buffer = ConversationBuffer(result_handler=handler)
        buffer.CLEANUP_INTERVAL_SECONDS = 0.01
        base_time = datetime.now(timezone.utc)

        failed_session = buffer.add(
            create_message(1, 100, "fail", base_time)
        )
        successful_session = buffer.add(
            create_message(2, 100, "success", base_time)
        )
        failed_session.last_message_at = base_time - timedelta(seconds=6)
        successful_session.last_message_at = base_time - timedelta(seconds=6)

        buffer.start_cleanup()
        await asyncio.sleep(0.05)
        await buffer.stop_cleanup()

        assert calls.count("fail") == 2
        assert calls.count("success") == 1
        assert buffer.sessions == {}
        assert buffer._pending_sessions == {}

    asyncio.run(run_test())


def test_conversation_result_contains_message_ids():

    buffer = ConversationBuffer()

    base_time = datetime.now(timezone.utc)

    message1 = create_message(
        author_id=1,
        channel_id=100,
        content="안",
        created_at=base_time,
    )

    message2 = create_message(
        author_id=1,
        channel_id=100,
        content="녕하세요",
        created_at=base_time + timedelta(seconds=1),
    )

    buffer.add(message1)
    buffer.add(message2)

    session = buffer.sessions[(1, 100)]

    result = session.to_result(
        language="ko"
    )

    assert result.message_ids == [
        message1.discord_message_id,
        message2.discord_message_id,
    ]

    assert result.language == "ko"
    assert result.text == "안 녕하세요"
