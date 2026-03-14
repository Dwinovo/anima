from __future__ import annotations

from src.core.exceptions import SessionNotFoundException
from src.domain.session.repository import SessionRepository


class DeleteSessionUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo

    async def execute(self, *, session_id: str) -> None:
        """执行业务流程并返回结果。"""
        existing = await self._session_repo.get(session_id=session_id)
        if existing is None:
            raise SessionNotFoundException(session_id)
        await self._session_repo.delete(session_id=session_id)
