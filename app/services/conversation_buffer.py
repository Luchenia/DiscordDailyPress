from datetime import datetime

from app.dto.discord_message_dto import DiscordMessageDTO

import asyncio

from app.services.language_service import LanguageService

from app.core.logger import get_logger
logger = get_logger(__name__)

from app.dto.conversation_result_dto import ConversationResultDTO

from typing import Callable


class ConversationSession:
    """
    AI 분석을 위한 하나의 대화 세션
    """

    def __init__(
        self,
        author_id: int,
        channel_id: int,
        first_message: DiscordMessageDTO,
    ):
        self.author_id = author_id
        self.channel_id = channel_id

        self.messages: list[DiscordMessageDTO] = [
            first_message
        ]

        self.started_at: datetime = first_message.created_at
        self.last_message_at: datetime = first_message.created_at

    def add_message(
        self,
        message: DiscordMessageDTO,
    ) -> None:

        self.messages.append(message)

        self.last_message_at = message.created_at


    def get_text(self) -> str:
        """
        세션에 포함된 메시지를 하나의 텍스트로 합친다.
        """

        return " ".join(
            message.content
            for message in self.messages
            if message.content.strip()
        )


    def to_result(
        self,
        language: str,
    ) -> ConversationResultDTO:

        return ConversationResultDTO(
            message_ids=[
                message.discord_message_id
                for message in self.messages
            ],

            author_id=self.author_id,
            channel_id=self.channel_id,

            text=self.get_text(),
            language=language,

            started_at=self.started_at,
            ended_at=self.last_message_at,
        )





class ConversationBuffer:
    """
    여러 사용자의 ConversationSession을 관리하는 버퍼
    """

    BUFFER_TIMEOUT_SECONDS = 5
    CLEANUP_INTERVAL_SECONDS = 1

    def __init__(
        self,
        result_handler: Callable[[ConversationResultDTO], None] | None = None,
    ):
        self.sessions: dict[
            tuple[int, int],
            ConversationSession,
        ] = {}

        self._cleanup_task: asyncio.Task | None = None

        self._pending_sessions: dict[
            int,
            ConversationSession,
        ] = {}

        self.language_service = LanguageService()

        self.result_handler = result_handler

    def add(
        self,
        message: DiscordMessageDTO,
    ) -> ConversationSession:

        key = (
            message.author_id,
            message.channel_id,
        )

        current_session = self.sessions.get(key)

        # 기존 세션이 없는 경우
        if current_session is None:
            session = ConversationSession(
                author_id=message.author_id,
                channel_id=message.channel_id,
                first_message=message,
            )

            self.sessions[key] = session

            return session

        # 마지막 메시지와 현재 메시지의 시간 차이
        elapsed = (
            message.created_at
            - current_session.last_message_at
        ).total_seconds()

        # 5초 이내라면 기존 세션에 추가
        if elapsed <= self.BUFFER_TIMEOUT_SECONDS:
            current_session.add_message(message)

            return current_session

        result = self._flush_session(
            self.sessions,
            key,
            current_session,
        )

        if result is None:
            if self.sessions.get(key) is current_session:
                del self.sessions[key]

            self._pending_sessions[id(current_session)] = current_session

        new_session = ConversationSession(
            author_id=message.author_id,
            channel_id=message.channel_id,
            first_message=message,
        )

        self.sessions[key] = new_session

        return new_session

    def start_cleanup(self) -> None:
        """
        만료된 ConversationSession을 정리하는 백그라운드 작업 시작
        """

        if (
            self._cleanup_task is not None
            and not self._cleanup_task.done()
        ):
            return

        logger.info("Starting conversation cleanup task")

        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop()
        )

    async def stop_cleanup(self) -> list[ConversationResultDTO]:
        """Stop the cleanup task and flush every buffered conversation."""
        task = self._cleanup_task
        self._cleanup_task = None

        if task is not None:
            if not task.done():
                task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                logger.info("Conversation cleanup task cancelled")
            except Exception:
                logger.exception(
                    "Conversation cleanup task ended unexpectedly"
                )

        return self.flush_all()

    async def _cleanup_loop(self) -> None:
        """
        주기적으로 만료된 세션을 확인한다.
        """

        logger.info("Conversation cleanup loop started")

        try:
            while True:
                await asyncio.sleep(
                    self.CLEANUP_INTERVAL_SECONDS
                )

                try:
                    results = self.flush_expired()

                    if results:
                        logger.info(
                            "Flushed %s conversation result(s)",
                            len(results),
                        )

                except Exception:
                    logger.exception(
                        "Conversation cleanup cycle failed"
                    )

        except asyncio.CancelledError:
            logger.info("Conversation cleanup loop stopped")
            raise

    def flush_expired(
        self,
    ) -> list[ConversationResultDTO]:

        results: list[ConversationResultDTO] = []

        for key, session in list(self.sessions.items()):
            if self._is_expired(session):
                result = self._flush_session(
                    self.sessions,
                    key,
                    session,
                )

                if result is not None:
                    results.append(result)

        results.extend(self._flush_pending_sessions())

        return results

    def flush_all(self) -> list[ConversationResultDTO]:
        """Flush all active and retry-pending conversations."""
        results: list[ConversationResultDTO] = []

        for key, session in list(self.sessions.items()):
            result = self._flush_session(
                self.sessions,
                key,
                session,
            )

            if result is not None:
                results.append(result)

        results.extend(self._flush_pending_sessions())

        return results

    def _flush_pending_sessions(self) -> list[ConversationResultDTO]:
        results: list[ConversationResultDTO] = []

        for session_id, session in list(
            self._pending_sessions.items()
        ):
            result = self._flush_session(
                self._pending_sessions,
                session_id,
                session,
            )

            if result is not None:
                results.append(result)

        return results

    def _is_expired(
        self,
        session: ConversationSession,
    ) -> bool:
        elapsed = (
            datetime.now(session.last_message_at.tzinfo)
            - session.last_message_at
        ).total_seconds()

        return elapsed > self.BUFFER_TIMEOUT_SECONDS

    def _flush_session(
        self,
        sessions: dict,
        key: tuple[int, int] | int,
        session: ConversationSession,
    ) -> ConversationResultDTO | None:
        try:
            text = session.get_text()
            language = self.language_service.detect(text)
            result = session.to_result(language=language)

            if self.result_handler is not None:
                self.result_handler(result)

        except Exception:
            logger.exception(
                "Failed to flush conversation for author=%s channel=%s",
                session.author_id,
                session.channel_id,
            )
            return None

        if sessions.get(key) is session:
            del sessions[key]

        logger.info(
            "Conversation ended: %s (language=%s)",
            result.text,
            result.language,
        )

        return result
