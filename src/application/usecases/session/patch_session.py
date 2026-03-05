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
        name: str | None = None,
        description: str | None = None,
        max_entities_limit: int | None = None,
    ) -> SessionDetailInfo:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        merged_name = session.name if name is None else name
        merged_description = session.description if description is None else description
        merged_max_entities_limit = session.max_entities_limit if max_entities_limit is None else max_entities_limit

        updated_session = await self._session_repo.update(
            session_id=session_id,
            name=merged_name,
            description=merged_description,
            max_entities_limit=merged_max_entities_limit,
        )
        if updated_session is None:
            raise SessionNotFoundException(session_id)

        return SessionDetailInfo(
            session_id=updated_session.session_id,
            name=updated_session.name,
            description=updated_session.description,
            max_entities_limit=updated_session.max_entities_limit,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
        )
