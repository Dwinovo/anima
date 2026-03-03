from __future__ import annotations

from dataclasses import dataclass

from src.domain.session.repository import SessionRepository


@dataclass(slots=True)
class SessionListInfo:
    """会话列表项基础信息。"""

    session_id: str
    name: str
    description: str | None
    max_agents_limit: int


class ListSessionsUseCase:
    """列出控制面中全部 Session。"""

    def __init__(self, session_repo: SessionRepository) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo

    async def execute(self) -> list[SessionListInfo]:
        """执行业务流程并返回结果。"""
        sessions = await self._session_repo.list()
        results: list[SessionListInfo] = []
        for session in sessions:
            results.append(
                SessionListInfo(
                    session_id=session.session_id,
                    name=session.name,
                    description=session.description,
                    max_agents_limit=session.max_agents_limit,
                )
            )
        return results
