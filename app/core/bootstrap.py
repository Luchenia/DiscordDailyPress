from app.core.config import config
from app.core.logger import get_logger
from app.database.base import Base
from app.database.session import engine

logger = get_logger(__name__)


def bootstrap() -> None:
    """
    프로젝트 시작 시 필요한 초기화 작업
    """

    # storage 폴더 생성
    config.storage_dir.mkdir(parents=True, exist_ok=True)
    config.database_dir.mkdir(parents=True, exist_ok=True)
    config.opus_dir.mkdir(parents=True, exist_ok=True)
    config.wav_dir.mkdir(parents=True, exist_ok=True)
    config.newspaper_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 50)
    logger.info("Project Chronicle Bootstrap")
    logger.info("Storage: %s", config.storage_dir)
    logger.info("Database: %s", config.database_dir)
    logger.info("Bootstrap completed successfully.")
    logger.info("=" * 50)

    Base.metadata.create_all(bind=engine)

    logger.info("Database initialized.")