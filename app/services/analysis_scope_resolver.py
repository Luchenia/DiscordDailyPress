from app.dto.analysis_request_dto import AnalysisRequestDTO
from app.dto.analysis_scope_dto import AnalysisScopeDTO
from app.repositories.collection_channel_repository import (
    CollectionChannelRepository,
)


class AnalysisScopeResolver:
    """
    분석 요청을 실제 분석 범위로 변환한다.
    """

    def __init__(
        self,
        repository: CollectionChannelRepository | None = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else CollectionChannelRepository()
        )

    def resolve(
        self,
        request: AnalysisRequestDTO,
    ) -> AnalysisScopeDTO:

        channel_ids = self.repository.get_enabled_channel_ids(
            request.guild_id,
        )

        if not channel_ids:
            raise ValueError(
                "분석 대상으로 활성화된 채널이 없습니다."
            )

        return AnalysisScopeDTO(
            guild_id=request.guild_id,
            channel_ids=channel_ids,
            start_at=request.start_at,
            end_at=request.end_at,
        )