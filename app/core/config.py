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
    gemini_translation_model: str = os.getenv(
        "GEMINI_TRANSLATION_MODEL", "gemini-3.5-flash-lite"
    )
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_translation_model: str = os.getenv(
        "NVIDIA_TRANSLATION_MODEL", "nvidia/riva-translate-4b-instruct-v2"
    )
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    google_credentials: str = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", ""
    )
    discord_guild_id: int = int(
        os.getenv("DISCORD_GUILD_ID", "0")
    )

    # Paths
    storage_dir: Path = BASE_DIR / "storage"
    database_dir: Path = storage_dir / "database"
    opus_dir: Path = storage_dir / "opus"
    wav_dir: Path = storage_dir / "wav"
    newspaper_dir: Path = storage_dir / "newspapers"


config = Config()
