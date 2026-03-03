from __future__ import annotations

from src.application.usecases.session.get_session import SessionDetailInfo
from src.core.exceptions import SessionNotFoundException
from src.domain.session.repository import SessionRepository


class PatchSessionUseCase:
    """增量更新指定 Session。"""

    def __init__(self, session_repo: SessionRepository) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo

    async def execute(
        self,
        *,
        session_id: str,
        description: str | None = None,
        max_agents_limit: int | None = None,
    ) -> SessionDetailInfo:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        merged_description = session.description if description is None else description
        merged_max_agents_limit = session.max_agents_limit if max_agents_limit is None else max_agents_limit

        updated_session = await self._session_repo.update(
            session_id=session_id,
            description=merged_description,
            max_agents_limit=merged_max_agents_limit,
        )
        if updated_session is None:
            raise SessionNotFoundException(session_id)

        return SessionDetailInfo(
            session_id=updated_session.session_id,
            description=updated_session.description,
            max_agents_limit=updated_session.max_agents_limit,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
        )
