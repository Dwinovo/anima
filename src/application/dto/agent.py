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
    token_type: str | None = None
    access_token: str | None = None
    access_token_expires_in: int | None = None
    refresh_token: str | None = None
    refresh_token_expires_in: int | None = None


@dataclass(slots=True)
class AgentContextResult:
    """Agent 社交上下文结果 DTO。"""

    session_id: str
    agent_id: str
    current_world_time: int
    status_events: list[EventSearchItem]
    media_public_events: list[EventSearchItem]
    media_following_events: list[EventSearchItem]
    self_events: list[EventSearchItem]


__all__ = ["AgentContextResult", "AgentLifecycleResult"]
