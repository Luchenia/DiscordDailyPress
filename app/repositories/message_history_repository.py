from app.database.session import SessionLocal
from app.models.message_history import MessageHistory


class MessageHistoryRepository:

    def save(
        self,
        history: MessageHistory,
    ) -> MessageHistory:

        with SessionLocal() as session:

            session.add(history)
            session.commit()
            session.refresh(history)

            return history