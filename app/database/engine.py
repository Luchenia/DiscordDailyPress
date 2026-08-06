from sqlalchemy import create_engine

from app.core.config import config

DATABASE_URL = (
    f"sqlite:///{config.database_dir / 'chronicle.db'}"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)