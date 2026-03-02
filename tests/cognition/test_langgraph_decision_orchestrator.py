from __future__ import annotations

import json

import pytest

from src.application.cognition.langgraph_orchestrator import LangGraphDecisionOrchestrator
from src.application.dto.event import EventReportResult, EventSearchItem, EventSearchResult
from src.core.exceptions import AgentNotFoundException
from src.domain.agent.social_actions import SocialActionCommand, SocialActionVerb


class InMemoryProfileRepository:
    def __init__(self, profile_json: str | None) -> None:
        """初始化 Profile 仓储测试替身。"""
        self._profile_json = profile_json

    async def get(self, *, session_id: str, uuid: str) -> str | None:
        """返回预设画像。"""
        _ = (session_id, uuid)
        return self._profile_json


class InMemoryCheckpointRepository:
    def __init__(self) -> None:
        """初始化 Checkpoint 仓储测试替身。"""
        self.saved_snapshots: list[str] = []
        self.saved_ttl_seconds: int | None = None

    async def load(self, *, session_id: str, uuid: str) -> list[str]:
        """返回预设短期记忆。"""
        _ = (session_id, uuid)
        return ["上一轮：先观望"]

    async def save(
        self,
        *,
        session_id: str,
        uuid: str,
        snapshots: list[str],
        ttl_seconds: int,
    ) -> None:
        """保存最新短期记忆快照。"""
        _ = (session_id, uuid)
        self.saved_snapshots = snapshots
        self.saved_ttl_seconds = ttl_seconds


class FakeSearchEventsUseCase:
    async def execute(
        self,
        *,
        session_id: str,
        anchor_uuid: str,
        limit: int,
        candidate_limit: int,
    ) -> EventSearchResult:
        """返回预设检索结果。"""
        _ = (session_id, anchor_uuid, limit, candidate_limit)
        return EventSearchResult(
            session_id="session_demo",
            items=[
                EventSearchItem(
                    event_id="event_prev",
                    world_time=99,
                    verb="POSTED",
                    subject_uuid="agent_b",
                    target_ref="board:session_demo",
                    details={"content": "hello"},
                    schema_version=1,
                    is_social=True,
                )
            ],
            total=1,
        )


class FakeReportEventUseCase:
    def __init__(self) -> None:
        """初始化上报用例测试替身。"""
        self.last_kwargs: dict[str, object] | None = None

    async def execute(self, **kwargs: object) -> EventReportResult:
        """记录调用参数并返回 accepted 结果。"""
        self.last_kwargs = kwargs
        return EventReportResult(
            session_id=str(kwargs["session_id"]),
            event_id="event_new",
            world_time=int(kwargs["world_time"]),
            verb=str(kwargs["verb"]),
            accepted=True,
        )


class FakeDecisionModel:
    async def decide(self, **kwargs: object) -> SocialActionCommand:
        """返回固定 OBSERVED 动作，模拟 LLM 决策输出。"""
        _ = kwargs
        return SocialActionCommand(
            verb=SocialActionVerb.OBSERVED,
            target_ref="board:session_demo",
            details={"internal_thought": "先记录局势再行动"},
            inner_thought_brief="先观察局势",
            is_social=True,
        )


class FakeCompiledGraph:
    """LangGraph 编译结果测试替身。"""

    def __init__(self) -> None:
        """初始化调用记录。"""
        self.last_state: dict[str, object] | None = None
        self.last_config: dict[str, object] | None = None

    async def ainvoke(
        self,
        state: dict[str, object],
        config: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """记录入参与配置，并返回固定决策结果。"""
        self.last_state = state
        self.last_config = config
        return {
            "action_command": SocialActionCommand(
                verb=SocialActionVerb.OBSERVED,
                target_ref="board:session_demo",
                details={"internal_thought": "先记录局势再行动"},
                inner_thought_brief="先观察局势",
                is_social=True,
            ),
            "event_result": EventReportResult(
                session_id="session_demo",
                event_id="event_new",
                world_time=100,
                verb="OBSERVED",
                accepted=True,
            ),
        }


@pytest.mark.asyncio
async def test_langgraph_decision_orchestrator_runs_full_pipeline() -> None:
    """验证 LangGraph 编排闭环：检索、决策、上报、checkpoint。"""
    profile_repo = InMemoryProfileRepository(
        json.dumps(
            {
                "name": "Alice",
                "display_name": "Alice#10001",
                "profile": {"persona": "router"},
            },
            ensure_ascii=False,
        )
    )
    checkpoint_repo = InMemoryCheckpointRepository()
    search_usecase = FakeSearchEventsUseCase()
    report_usecase = FakeReportEventUseCase()
    decision_model = FakeDecisionModel()

    orchestrator = LangGraphDecisionOrchestrator(
        profile_repo=profile_repo,
        checkpoint_repo=checkpoint_repo,
        search_usecase=search_usecase,
        report_usecase=report_usecase,
        decision_model=decision_model,
        checkpoint_ttl_seconds=7200,
        working_memory_window=3,
    )

    result = await orchestrator.execute(
        session_id="session_demo",
        uuid="agent_a",
        world_time=100,
        recall_limit=3,
        candidate_limit=8,
    )

    assert result.session_id == "session_demo"
    assert result.uuid == "agent_a"
    assert result.event_id == "event_new"
    assert result.verb == "OBSERVED"
    assert result.target_ref == "board:session_demo"
    assert result.inner_thought_brief == "先观察局势"
    assert result.accepted is True
    assert report_usecase.last_kwargs is not None
    assert report_usecase.last_kwargs["target_ref"] == "board:session_demo"
    assert checkpoint_repo.saved_ttl_seconds == 7200
    assert checkpoint_repo.saved_snapshots[-1] == "先观察局势"


@pytest.mark.asyncio
async def test_langgraph_decision_orchestrator_raises_when_profile_missing() -> None:
    """验证 Profile 缺失时会中断决策流程。"""
    orchestrator = LangGraphDecisionOrchestrator(
        profile_repo=InMemoryProfileRepository(None),
        checkpoint_repo=InMemoryCheckpointRepository(),
        search_usecase=FakeSearchEventsUseCase(),
        report_usecase=FakeReportEventUseCase(),
        decision_model=FakeDecisionModel(),
        checkpoint_ttl_seconds=7200,
        working_memory_window=3,
    )

    with pytest.raises(AgentNotFoundException):
        await orchestrator.execute(
            session_id="session_demo",
            uuid="agent_a",
            world_time=100,
            recall_limit=3,
            candidate_limit=8,
        )


@pytest.mark.asyncio
async def test_langgraph_decision_orchestrator_passes_thread_config_to_graph() -> None:
    """验证编排器调用 LangGraph 时会附带线程配置。"""
    orchestrator = LangGraphDecisionOrchestrator(
        profile_repo=InMemoryProfileRepository('{"name":"Alice","display_name":"Alice#10001","profile":{}}'),
        checkpoint_repo=InMemoryCheckpointRepository(),
        search_usecase=FakeSearchEventsUseCase(),
        report_usecase=FakeReportEventUseCase(),
        decision_model=FakeDecisionModel(),
        checkpoint_ttl_seconds=7200,
        working_memory_window=3,
    )
    fake_graph = FakeCompiledGraph()
    orchestrator._graph = fake_graph

    await orchestrator.execute(
        session_id="session_demo",
        uuid="agent_a",
        world_time=100,
        recall_limit=3,
        candidate_limit=8,
    )

    assert fake_graph.last_state is not None
    assert fake_graph.last_state["session_id"] == "session_demo"
    assert fake_graph.last_config == {
        "configurable": {
            "thread_id": "session_demo:agent_a",
            "checkpoint_ns": "agent_decision",
        }
    }
