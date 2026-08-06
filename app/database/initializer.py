from app.database.base import Base
from app.database.engine import engine

# 모델 등록
from app.models.message import Message


def initialize_database() -> None:
    """
    데이터베이스와 테이블을 생성한다.
    """
    Base.metadata.create_all(bind=engine)