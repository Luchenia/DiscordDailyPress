from app.database.session import SessionLocal
from app.models.message_delete_history import MessageDeleteHistory


class MessageDeleteHistoryRepository:

    def save(
        self,
        history: MessageDeleteHistory,
    ) -> MessageDeleteHistory:

        with SessionLocal() as session:

            session.add(history)

            session.commit()

            session.refresh(history)

            return history