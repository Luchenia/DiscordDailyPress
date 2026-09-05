from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.message_history import MessageHistory


class MessageHistoryRepository:

    def save(
        self,
        history: MessageHistory,
        session: Session | None = None,
    ) -> MessageHistory:
        if session is not None:
            return self._save(session, history)

        with SessionLocal.begin() as session:
            return self._save(session, history)

    @staticmethod
    def _save(
        session: Session,
        history: MessageHistory,
    ) -> MessageHistory:
        latest_version = session.scalar(
            select(func.max(MessageHistory.version)).where(
                MessageHistory.message_id == history.message_id
            )
        )

        history.version = (latest_version or 0) + 1
        session.add(history)
        session.flush()

        return history
