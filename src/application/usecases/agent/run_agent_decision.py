from __future__ import annotations

from src.application.cognition.orchestrator import AgentDecisionOrchestrator
from src.application.dto.decision import AgentDecisionResult
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.agent.presence_repository import AgentPresenceRepository
from src.domain.session.repository import SessionRepository


class RunAgentDecisionUseCase:
    """触发并执行一次 Agent 认知决策闭环。"""

    def __init__(
        self,
        *,
        session_repo: SessionRepository,
        presence_repo: AgentPresenceRepository,
        orchestrator: AgentDecisionOrchestrator,
    ) -> None:
        """初始化对象并注入所需依赖。"""
        self._session_repo = session_repo
        self._presence_repo = presence_repo
        self._orchestrator = orchestrator

    async def execute(
        self,
        *,
        session_id: str,
        uuid: str,
        world_time: int,
        recall_limit: int,
        candidate_limit: int,
    ) -> AgentDecisionResult:
        """执行 UseCase 并返回决策结果。"""
        session = await self._session_repo.get(session_id=session_id)
        if session is None:
            raise SessionNotFoundException(session_id)

        active = await self._presence_repo.is_active(session_id=session_id, uuid=uuid)
        if not active:
            raise AgentNotFoundException(session_id=session_id, uuid=uuid)

        return await self._orchestrator.execute(
            session_id=session_id,
            uuid=uuid,
            world_time=world_time,
            recall_limit=recall_limit,
            candidate_limit=candidate_limit,
        )
