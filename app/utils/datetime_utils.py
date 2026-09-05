from datetime import UTC
from datetime import datetime
from zoneinfo import ZoneInfo


KST = ZoneInfo("Asia/Seoul")


def ensure_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime, treating legacy naive SQLite values as UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def to_kst(value: datetime) -> datetime:
    return ensure_utc(value).astimezone(KST)
