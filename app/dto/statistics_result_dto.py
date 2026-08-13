from pydantic import BaseModel


class AuthorMessageCountDTO(BaseModel):
    """
    사용자별 메시지 작성 수
    """

    author_id: int
    author_display_name: str
    message_count: int


class ChannelMessageCountDTO(BaseModel):
    """
    채널별 메시지 수
    """

    channel_id: int
    channel_name: str
    message_count: int


class DailyMessageCountDTO(BaseModel):
    """
    날짜별 메시지 수
    """

    date: str
    message_count: int


class HourlyMessageCountDTO(BaseModel):
    """
    시간대별 메시지 수
    """

    hour: int
    message_count: int


class StatisticsResultDTO(BaseModel):
    """
    AnalysisDataset에서 계산된 통계 결과
    """

    message_count: int
    author_count: int
    channel_count: int

    top_authors: list[AuthorMessageCountDTO]
    channel_activity: list[ChannelMessageCountDTO]

    daily_activity: list[DailyMessageCountDTO]
    hourly_activity: list[HourlyMessageCountDTO]

    language_distribution: dict[str, float]