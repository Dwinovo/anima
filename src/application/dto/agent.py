from __future__ import annotations

from dataclasses import dataclass

from src.application.dto.event import EventSearchItem


@dataclass(slots=True)
class AgentLifecycleResult:
    """Agent 生命周期操作结果 DTO。"""

    session_id: str
    agent_id: str
    active: bool
    name: str | None = None
    display_name: str | None = None
    profile: str | None = None


@dataclass(slots=True)
class AgentContextResult:
    """Agent 社交上下文结果 DTO。"""

    session_id: str
    agent_id: str
    status_events: list[EventSearchItem]
    media_events: list[EventSearchItem]


__all__ = ["AgentContextResult", "AgentLifecycleResult"]
