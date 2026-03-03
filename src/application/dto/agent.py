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
class AgentContextEventListView:
    """Agent 上下文事件流视图 DTO。"""

    items: list[EventSearchItem]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class AgentContextHotTopic:
    """Agent 上下文热点项 DTO。"""

    topic_ref: str
    score: float
    sample_event_ids: list[str]


@dataclass(slots=True)
class AgentContextHotListView:
    """Agent 上下文热点视图 DTO。"""

    items: list[AgentContextHotTopic]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class AgentContextWorldSnapshot:
    """Agent 上下文世界快照 DTO。"""

    online_agents: int
    active_agents: int
    recent_event_count: int
    my_following_count: int


@dataclass(slots=True)
class AgentContextViews:
    """Agent 上下文六视图 DTO。"""

    self_recent: AgentContextEventListView
    public_feed: AgentContextEventListView
    following_feed: AgentContextEventListView
    attention: AgentContextEventListView
    hot: AgentContextHotListView
    world_snapshot: AgentContextWorldSnapshot


@dataclass(slots=True)
class AgentContextResult:
    """Agent 社交上下文结果 DTO。"""

    session_id: str
    agent_id: str
    current_world_time: int
    views: AgentContextViews


__all__ = [
    "AgentContextEventListView",
    "AgentContextHotListView",
    "AgentContextHotTopic",
    "AgentContextResult",
    "AgentContextViews",
    "AgentContextWorldSnapshot",
    "AgentLifecycleResult",
]
