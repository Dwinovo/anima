from __future__ import annotations

from uuid import uuid4

from src.domain.session.entities import Session
from src.domain.session.repository import SessionRepository


class CreateSessionUseCase:
    def __init__(self, session_repo: SessionRepository, *, default_llm_model: str) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._default_llm_model = default_llm_model

    async def execute(
        self,
        *,
        name: str,
        description: str | None,
        max_agents_limit: int,
        default_llm: str | None,
    ) -> Session:
        """执行业务流程并返回结果。"""
        session_id = f"session_{uuid4().hex[:8]}"
        selected_model = default_llm or self._default_llm_model
        return await self._session_repo.create(
            session_id=session_id,
            max_agents_limit=max_agents_limit,
            default_llm=selected_model,
            name=name,
            description=description,
        )
