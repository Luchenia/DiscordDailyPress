from datetime import UTC, datetime, timedelta

from app.utils.datetime_utils import KST, ensure_utc



class AnalysisPeriodService:

    def resolve(
        self,
        period: str,
        now: datetime | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[datetime, datetime]:

        if now is None:

            now = datetime.now(UTC)

        now = ensure_utc(now)

        # 현재 시각을 한국 시간으로 변환
        local_now = now.astimezone(
            KST,
        )

        if period == "오늘":

            local_start = local_now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            return (
                local_start.astimezone(
                    UTC,
                ),
                now,
            )

        if period == "이번주":

            local_start = (
                local_now
                - timedelta(
                    days=local_now.weekday(),
                )
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            return (
                local_start.astimezone(
                    UTC,
                ),
                now,
            )

        if period == "이번달":

            local_start = local_now.replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            return (
                local_start.astimezone(
                    UTC,
                ),
                now,
            )

        if period == "올해":

            local_start = local_now.replace(
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            return (
                local_start.astimezone(
                    UTC,
                ),
                now,
            )

        if period == "직접입력":

            # 시작일은 반드시 필요
            if start_date is None:

                raise ValueError(
                    "직접입력 기간은 시작일을 입력해야 합니다."
                )

            try:

                local_start = datetime.strptime(
                    start_date,
                    "%Y-%m-%d",
                ).replace(
                    tzinfo=KST,
                )

                # 종료일을 입력하지 않았다면
                # 시작일부터 현재까지 분석
                if end_date is None:

                    if local_start > local_now:

                        raise ValueError(
                            "시작일은 오늘보다 이후일 수 없습니다."
                        )

                    return (
                        local_start.astimezone(
                            UTC,
                        ),
                        now,
                    )

                local_end = datetime.strptime(
                    end_date,
                    "%Y-%m-%d",
                ).replace(
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=999999,
                    tzinfo=KST,
                )

            except ValueError as error:

                if str(error) in (
                    "시작일은 오늘보다 이후일 수 없습니다.",
                ):
                    raise

                raise ValueError(
                    "날짜는 YYYY-MM-DD 형식으로 입력해야 합니다."
                )

            if local_start > local_end:

                raise ValueError(
                    "시작일은 종료일보다 이전이어야 합니다."
                )

            return (
                local_start.astimezone(
                    UTC,
                ),
                local_end.astimezone(
                    UTC,
                ),
            )

        raise ValueError(
            "알 수 없는 분석 기간입니다."
        )
