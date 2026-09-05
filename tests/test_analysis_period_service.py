from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.services.analysis_period_service import (
    AnalysisPeriodService,
)


KST = ZoneInfo("Asia/Seoul")


def test_today():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start_at, end_at = service.resolve(
        period="오늘",
        now=now,
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        18,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at == now


def test_this_week():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start_at, end_at = service.resolve(
        period="이번주",
        now=now,
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        17,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at == now


def test_this_month():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start_at, end_at = service.resolve(
        period="이번달",
        now=now,
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        1,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at == now


def test_this_year():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start_at, end_at = service.resolve(
        period="올해",
        now=now,
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        1,
        1,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at == now


def test_custom_period():

    service = AnalysisPeriodService()

    start_at, end_at = service.resolve(
        period="직접입력",
        start_date="2026-08-01",
        end_date="2026-08-14",
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        1,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at.astimezone(KST) == datetime(
        2026,
        8,
        14,
        23,
        59,
        59,
        999999,
        tzinfo=KST,
    )
    assert start_at == datetime(
        2026,
        7,
        31,
        15,
        tzinfo=timezone.utc,
    )
    assert end_at == datetime(
        2026,
        8,
        14,
        14,
        59,
        59,
        999999,
        tzinfo=timezone.utc,
    )


def test_custom_period_start_only():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    start_at, end_at = service.resolve(
        period="직접입력",
        now=now,
        start_date="2026-08-01",
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        1,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at == now


def test_custom_period_supports_same_date():

    service = AnalysisPeriodService()

    start_at, end_at = service.resolve(
        period="직접입력",
        start_date="2026-08-14",
        end_date="2026-08-14",
    )

    assert start_at.astimezone(KST) == datetime(
        2026,
        8,
        14,
        0,
        0,
        0,
        tzinfo=KST,
    )

    assert end_at.astimezone(KST) == datetime(
        2026,
        8,
        14,
        23,
        59,
        59,
        999999,
        tzinfo=KST,
    )


def test_custom_period_requires_start_date():

    service = AnalysisPeriodService()

    try:

        service.resolve(
            period="직접입력",
            end_date="2026-08-14",
        )

    except ValueError as error:

        assert "시작일" in str(error)

    else:

        raise AssertionError(
            "시작일 없이 직접입력을 허용하면 안 됩니다."
        )


def test_custom_period_rejects_future_start_date():

    service = AnalysisPeriodService()

    now = datetime(
        2026,
        8,
        18,
        14,
        30,
        tzinfo=timezone.utc,
    )

    try:

        service.resolve(
            period="직접입력",
            now=now,
            start_date="2026-08-19",
        )

    except ValueError as error:

        assert "오늘보다 이후" in str(error)

    else:

        raise AssertionError(
            "미래 시작일을 허용하면 안 됩니다."
        )


def test_custom_period_rejects_invalid_date():

    service = AnalysisPeriodService()

    try:

        service.resolve(
            period="직접입력",
            start_date="2026/08/01",
        )

    except ValueError as error:

        assert "YYYY-MM-DD" in str(error)

    else:

        raise AssertionError(
            "잘못된 날짜 형식을 허용하면 안 됩니다."
        )


def test_custom_period_rejects_reversed_range():

    service = AnalysisPeriodService()

    try:

        service.resolve(
            period="직접입력",
            start_date="2026-08-14",
            end_date="2026-08-01",
        )

    except ValueError as error:

        assert "이전" in str(error)

    else:

        raise AssertionError(
            "역순 기간을 허용하면 안 됩니다."
        )


def test_invalid_period():

    service = AnalysisPeriodService()

    try:

        service.resolve(
            period="알수없음",
        )

    except ValueError as error:

        assert "분석 기간" in str(error)

    else:

        raise AssertionError(
            "알 수 없는 분석 기간을 허용하면 안 됩니다."
        )
