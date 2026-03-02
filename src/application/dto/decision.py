from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentDecisionResult:
    """Agent 决策执行结果 DTO。"""

    session_id: str
    uuid: str
    event_id: str
    verb: str
    target_ref: str
    inner_thought_brief: str
    accepted: bool


__all__ = ["AgentDecisionResult"]
