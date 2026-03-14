from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.core.exceptions import SessionNotFoundException
from src.domain.session.actions import SessionAction
from src.domain.session.entities import Session
from src.domain.session.repository import SessionRepository


@dataclass(slots=True)
class SessionDetailInfo:
    """Session 详情返回 DTO。"""

    session_id: str
    name: str
    description: str | None
    max_entities_limit: int
    actions: tuple[SessionAction, ...]
    created_at: datetime
    updated_at: datetime


class GetSessionUseCase:
    """查询指定 Session 详情。"""

    def __init__(self, session_repo: SessionRepository) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo

    async def execute(self, *, session_id: str) -> SessionDetailInfo:
        """执行业务流程并返回结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)
        return self._to_info(session)

    @staticmethod
    def _to_info(session: Session) -> SessionDetailInfo:
        """将 Session 实体映射为详情 DTO。"""
        return SessionDetailInfo(
            session_id=session.session_id,
            name=session.name,
            description=session.description,
            max_entities_limit=session.max_entities_limit,
            actions=session.actions,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
