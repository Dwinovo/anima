from __future__ import annotations

from uuid import uuid4

from src.domain.session.entities import Session
from src.domain.session.repository import SessionRepository


class CreateSessionUseCase:
    def __init__(self, session_repo: SessionRepository) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo

    async def execute(
        self,
        *,
        name: str,
        description: str | None,
        max_agents_limit: int,
    ) -> Session:
        """执行业务流程并返回结果。"""
        session_id = str(uuid4())
        return await self._session_repo.create(
            session_id=session_id,
            name=name,
            max_agents_limit=max_agents_limit,
            description=description,
        )
