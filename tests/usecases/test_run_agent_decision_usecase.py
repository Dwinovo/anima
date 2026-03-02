from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from src.application.dto.decision import AgentDecisionResult
from src.application.usecases.agent.run_agent_decision import RunAgentDecisionUseCase
from src.core.exceptions import AgentNotFoundException, SessionNotFoundException
from src.domain.session.entities import Session


class InMemorySessionRepository:
    def __init__(self, session: Session | None) -> None:
        """初始化 Session 仓储测试替身。"""
        self._session = session

    async def get(self, *, session_id: str) -> Session | None:
        """按 session_id 返回预设结果。"""
        if self._session is None:
            return None
        if self._session.session_id != session_id:
            return None
        return self._session


class InMemoryPresenceRepository:
    def __init__(self, *, active: bool) -> None:
        """初始化 Presence 仓储测试替身。"""
        self._active = active

    async def is_active(self, *, session_id: str, uuid: str) -> bool:
        """返回预设在线状态。"""
        _ = (session_id, uuid)
        return self._active


@dataclass(slots=True)
class FakeOrchestrator:
    result: AgentDecisionResult

    async def execute(
        self,
        *,
        session_id: str,
        uuid: str,
        world_time: int,
        recall_limit: int,
        candidate_limit: int,
    ) -> AgentDecisionResult:
        """返回预设编排结果。"""
        _ = (session_id, uuid, world_time, recall_limit, candidate_limit)
        return self.result


@pytest.mark.asyncio
async def test_run_agent_decision_usecase_raises_when_session_missing() -> None:
    """验证 Session 不存在时会抛出异常。"""
    usecase = RunAgentDecisionUseCase(
        session_repo=InMemorySessionRepository(None),
        presence_repo=InMemoryPresenceRepository(active=True),
        orchestrator=FakeOrchestrator(
            AgentDecisionResult(
                session_id="session_demo",
                uuid="agent_a",
                event_id="event_x",
                verb="OBSERVED",
                target_ref="board:session_demo",
                inner_thought_brief="先观察局势",
                accepted=True,
            )
        ),
    )

    with pytest.raises(SessionNotFoundException):
        await usecase.execute(
            session_id="session_demo",
            uuid="agent_a",
            world_time=100,
            recall_limit=3,
            candidate_limit=8,
        )


@pytest.mark.asyncio
async def test_run_agent_decision_usecase_raises_when_agent_inactive() -> None:
    """验证 Agent 不在线时会抛出异常。"""
    usecase = RunAgentDecisionUseCase(
        session_repo=InMemorySessionRepository(
            Session(
                session_id="session_demo",
                name="Demo",
                description=None,
                max_agents_limit=100,
                default_llm="gpt-4o",
                created_at=datetime.now(timezone.utc),
                updated_at=None,
            )
        ),
        presence_repo=InMemoryPresenceRepository(active=False),
        orchestrator=FakeOrchestrator(
            AgentDecisionResult(
                session_id="session_demo",
                uuid="agent_a",
                event_id="event_x",
                verb="OBSERVED",
                target_ref="board:session_demo",
                inner_thought_brief="先观察局势",
                accepted=True,
            )
        ),
    )

    with pytest.raises(AgentNotFoundException):
        await usecase.execute(
            session_id="session_demo",
            uuid="agent_a",
            world_time=100,
            recall_limit=3,
            candidate_limit=8,
        )


@pytest.mark.asyncio
async def test_run_agent_decision_usecase_returns_orchestrator_result() -> None:
    """验证 UseCase 会返回编排器输出。"""
    expected = AgentDecisionResult(
        session_id="session_demo",
        uuid="agent_a",
        event_id="event_x",
        verb="OBSERVED",
        target_ref="board:session_demo",
        inner_thought_brief="先观察局势",
        accepted=True,
    )
    usecase = RunAgentDecisionUseCase(
        session_repo=InMemorySessionRepository(
            Session(
                session_id="session_demo",
                name="Demo",
                description=None,
                max_agents_limit=100,
                default_llm="gpt-4o",
                created_at=datetime.now(timezone.utc),
                updated_at=None,
            )
        ),
        presence_repo=InMemoryPresenceRepository(active=True),
        orchestrator=FakeOrchestrator(expected),
    )

    result = await usecase.execute(
        session_id="session_demo",
        uuid="agent_a",
        world_time=100,
        recall_limit=3,
        candidate_limit=8,
    )

    assert result == expected
