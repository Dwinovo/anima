from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.application.cognition.decision_model import SocialDecisionModel
from src.application.cognition.orchestrator import AgentDecisionOrchestrator
from src.application.dto.decision import AgentDecisionResult
from src.application.dto.event import EventReportResult, EventSearchItem
from src.application.usecases.event.report_event import ReportEventUseCase
from src.application.usecases.event.search_events import SearchEventsUseCase
from src.core.exceptions import AgentNotFoundException
from src.domain.agent.checkpoint_repository import AgentCheckpointRepository
from src.domain.agent.profile_repository import AgentProfileRepository
from src.domain.agent.social_actions import SocialActionCommand


class DecisionGraphState(TypedDict, total=False):
    """LangGraph 编排状态。"""

    session_id: str
    uuid: str
    world_time: int
    recall_limit: int
    candidate_limit: int
    profile_payload: dict[str, Any]
    working_memory: list[str]
    observation_items: list[EventSearchItem]
    prompt: str
    action_command: SocialActionCommand
    event_result: EventReportResult


class LangGraphDecisionOrchestrator(AgentDecisionOrchestrator):
    """基于 LangGraph 的 Agent 决策编排器。"""

    def __init__(
        self,
        *,
        profile_repo: AgentProfileRepository,
        checkpoint_repo: AgentCheckpointRepository,
        search_usecase: SearchEventsUseCase,
        report_usecase: ReportEventUseCase,
        decision_model: SocialDecisionModel,
        checkpoint_ttl_seconds: int,
        working_memory_window: int,
        checkpointer: Any | None = None,
        checkpoint_namespace: str = "agent_decision",
    ) -> None:
        """初始化对象并注入编排所需依赖。"""
        self._profile_repo = profile_repo
        self._checkpoint_repo = checkpoint_repo
        self._search_usecase = search_usecase
        self._report_usecase = report_usecase
        self._decision_model = decision_model
        self._checkpoint_ttl_seconds = checkpoint_ttl_seconds
        self._working_memory_window = working_memory_window
        self._checkpointer = checkpointer
        self._checkpoint_namespace = checkpoint_namespace
        self._graph = self._build_graph()

    async def execute(
        self,
        *,
        session_id: str,
        uuid: str,
        world_time: int,
        recall_limit: int,
        candidate_limit: int,
    ) -> AgentDecisionResult:
        """执行一次完整的 LangGraph 决策流转。"""
        state: DecisionGraphState = {
            "session_id": session_id,
            "uuid": uuid,
            "world_time": world_time,
            "recall_limit": recall_limit,
            "candidate_limit": candidate_limit,
        }
        final_state = await self._graph.ainvoke(
            state,
            config=self._build_graph_config(session_id=session_id, uuid=uuid),
        )

        action_command = final_state["action_command"]
        event_result = final_state["event_result"]
        return AgentDecisionResult(
            session_id=session_id,
            uuid=uuid,
            event_id=event_result.event_id,
            verb=action_command.verb.value,
            target_ref=action_command.target_ref,
            inner_thought_brief=action_command.inner_thought_brief,
            accepted=event_result.accepted,
        )

    def _build_graph(self) -> Any:
        """构建 LangGraph 状态机并返回可执行图对象。"""
        graph = StateGraph(DecisionGraphState)
        graph.add_node("load_profile", self._load_profile)
        graph.add_node("load_working_memory", self._load_working_memory)
        graph.add_node("retrieve_observation", self._retrieve_observation)
        graph.add_node("assemble_prompt", self._assemble_prompt)
        graph.add_node("decide_action", self._decide_action)
        graph.add_node("report_event", self._report_event)
        graph.add_node("save_checkpoint", self._save_checkpoint)

        graph.add_edge(START, "load_profile")
        graph.add_edge("load_profile", "load_working_memory")
        graph.add_edge("load_working_memory", "retrieve_observation")
        graph.add_edge("retrieve_observation", "assemble_prompt")
        graph.add_edge("assemble_prompt", "decide_action")
        graph.add_edge("decide_action", "report_event")
        graph.add_edge("report_event", "save_checkpoint")
        graph.add_edge("save_checkpoint", END)

        return graph.compile(checkpointer=self._checkpointer)

    def _build_graph_config(self, *, session_id: str, uuid: str) -> dict[str, dict[str, str]]:
        """构建 LangGraph 调用配置，用于线程级状态持久化。"""
        return {
            "configurable": {
                "thread_id": self._build_thread_id(session_id=session_id, uuid=uuid),
                "checkpoint_ns": self._checkpoint_namespace,
            }
        }

    @staticmethod
    def _build_thread_id(*, session_id: str, uuid: str) -> str:
        """构建 `session_id + uuid` 组合线程标识。"""
        return f"{session_id}:{uuid}"

    async def _load_profile(self, state: DecisionGraphState) -> DecisionGraphState:
        """加载 Agent Profile（灵魂）并注入状态。"""
        session_id = state["session_id"]
        uuid = state["uuid"]
        profile_json = await self._profile_repo.get(session_id=session_id, uuid=uuid)
        if profile_json is None:
            raise AgentNotFoundException(session_id=session_id, uuid=uuid)
        profile_payload = self._parse_profile_payload(profile_json)
        return {"profile_payload": profile_payload}

    async def _load_working_memory(self, state: DecisionGraphState) -> DecisionGraphState:
        """加载短期工作记忆快照。"""
        snapshots = await self._checkpoint_repo.load(
            session_id=state["session_id"],
            uuid=state["uuid"],
        )
        return {"working_memory": snapshots}

    async def _retrieve_observation(self, state: DecisionGraphState) -> DecisionGraphState:
        """执行 recent-only 检索，拉取图谱观察视区。"""
        result = await self._search_usecase.execute(
            session_id=state["session_id"],
            anchor_uuid=state["uuid"],
            limit=state["recall_limit"],
            candidate_limit=state["candidate_limit"],
        )
        return {"observation_items": result.items}

    async def _assemble_prompt(self, state: DecisionGraphState) -> DecisionGraphState:
        """组装 human message 上下文。"""
        working_memory = state.get("working_memory", [])
        observation_items = state.get("observation_items", [])

        prompt_sections = [
            "# [RECENT MEMORY]",
            self._format_recent_memory_section(working_memory=working_memory),
            "",
            "# [OBSERVATION]",
            self._format_observation_section(observation_items=observation_items),
        ]
        return {"prompt": "\n".join(prompt_sections)}

    async def _decide_action(self, state: DecisionGraphState) -> DecisionGraphState:
        """调用决策模型输出社交动作命令。"""
        action_command = await self._decision_model.decide(
            session_id=state["session_id"],
            uuid=state["uuid"],
            prompt=state.get("prompt", ""),
            profile_payload=state.get("profile_payload", {}),
            working_memory=state.get("working_memory", []),
            observation_items=state.get("observation_items", []),
        )
        return {"action_command": action_command}

    async def _report_event(self, state: DecisionGraphState) -> DecisionGraphState:
        """将决策动作固化为 Event。"""
        command = state["action_command"]
        result = await self._report_usecase.execute(
            session_id=state["session_id"],
            world_time=state["world_time"],
            subject_uuid=state["uuid"],
            target_ref=command.target_ref,
            verb=command.verb.value,
            details=command.details,
            schema_version=1,
            is_social=command.is_social,
            embedding_256=None,
        )
        return {"event_result": result}

    async def _save_checkpoint(self, state: DecisionGraphState) -> DecisionGraphState:
        """写入最新短期记忆快照并设置 TTL。"""
        snapshots = list(state.get("working_memory", []))
        snapshots.append(state["action_command"].inner_thought_brief)
        snapshots = snapshots[-self._working_memory_window :]

        await self._checkpoint_repo.save(
            session_id=state["session_id"],
            uuid=state["uuid"],
            snapshots=snapshots,
            ttl_seconds=self._checkpoint_ttl_seconds,
        )
        return {"working_memory": snapshots}

    @staticmethod
    def _parse_profile_payload(profile_json: str) -> dict[str, Any]:
        """解析 Profile JSON，失败时降级为空字典。"""
        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError:
            return {}
        if isinstance(payload, dict):
            return payload
        return {}

    @staticmethod
    def _format_recent_memory_section(*, working_memory: list[str]) -> str:
        """格式化短期工作记忆视区。"""
        if not working_memory:
            return "- (empty)"
        return "\n".join(f"- {item}" for item in working_memory)

    @staticmethod
    def _format_observation_section(*, observation_items: list[EventSearchItem]) -> str:
        """格式化图谱观察视区。"""
        if not observation_items:
            return "- (empty)"
        lines: list[str] = []
        for item in observation_items:
            lines.append(
                f"- ({item.world_time}) [{item.verb}] {item.subject_uuid} -> {item.target_ref}: "
                f"{json.dumps(item.details, ensure_ascii=False)}"
            )
        return "\n".join(lines)
