from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

# 프로젝트 루트
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# .env 로드
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Config:
    """프로젝트 전역 설정"""

    # API Keys
    discord_bot_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    google_credentials: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )

    # Paths
    storage_dir: Path = BASE_DIR / "storage"
    database_dir: Path = storage_dir / "database"
    opus_dir: Path = storage_dir / "opus"
    wav_dir: Path = storage_dir / "wav"
    newspaper_dir: Path = storage_dir / "newspapers"


config = Config()