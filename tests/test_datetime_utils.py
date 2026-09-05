from datetime import UTC
from datetime import datetime
from zoneinfo import ZoneInfo

from app.utils.datetime_utils import ensure_utc
from app.utils.datetime_utils import to_kst


def test_ensure_utc_interprets_legacy_naive_datetime_as_utc():
    legacy_value = datetime(2026, 8, 1, 15, 0)

    assert ensure_utc(legacy_value) == datetime(
        2026,
        8,
        1,
        15,
        0,
        tzinfo=UTC,
    )


def test_to_kst_converts_utc_across_the_local_date_boundary():
    value = datetime(2026, 8, 1, 15, 0, tzinfo=UTC)

    assert to_kst(value) == datetime(
        2026,
        8,
        2,
        0,
        0,
        tzinfo=ZoneInfo("Asia/Seoul"),
    )
