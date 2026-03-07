from __future__ import annotations

from typing import Any
from uuid import uuid4

from src.domain.session.actions import session_actions_from_payload
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
        max_entities_limit: int,
        actions: list[dict[str, Any]],
    ) -> Session:
        """执行业务流程并返回结果。"""
        session_id = str(uuid4())
        return await self._session_repo.create(
            session_id=session_id,
            name=name,
            max_entities_limit=max_entities_limit,
            actions=session_actions_from_payload(actions),
            description=description,
        )
