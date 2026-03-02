from __future__ import annotations

from typing import Protocol

from src.application.dto.decision import AgentDecisionResult


class AgentDecisionOrchestrator(Protocol):
    """Agent 决策编排器接口。"""

    async def execute(
        self,
        *,
        session_id: str,
        uuid: str,
        world_time: int,
        recall_limit: int,
        candidate_limit: int,
    ) -> AgentDecisionResult:
        """执行一次完整认知闭环并返回决策结果。"""
        ...
