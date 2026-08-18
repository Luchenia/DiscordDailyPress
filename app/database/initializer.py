from app.database.base import Base
from app.database.engine import engine
import app.models


def initialize_database() -> None:
    """
    데이터베이스와 테이블을 생성한다.
    """

    Base.metadata.create_all(
        bind=engine,
    )