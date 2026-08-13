from pydantic import BaseModel

from app.dto.analysis_message_dto import AnalysisMessageDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO


class AnalysisDatasetMetadataDTO(BaseModel):
    """
    분석 대상 데이터의 파생 통계 정보
    """

    message_count: int
    author_count: int
    channel_count: int

    language_distribution: dict[str, float]


class AnalysisDatasetDTO(BaseModel):
    """
    특정 분석 범위에서 추출된 분석용 데이터셋
    """

    scope: AnalysisScopeDTO

    messages: list[AnalysisMessageDTO]

    metadata: AnalysisDatasetMetadataDTO