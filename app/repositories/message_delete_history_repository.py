from app.database.session import SessionLocal
from app.models.message_delete_history import MessageDeleteHistory
from sqlalchemy.orm import Session


class MessageDeleteHistoryRepository:

    def save(
        self,
        history: MessageDeleteHistory,
        session: Session | None = None,
    ) -> MessageDeleteHistory:
        if session is not None:
            session.add(history)
            return history

        with SessionLocal() as session:

            session.add(history)

            session.commit()

            session.refresh(history)

            return history
