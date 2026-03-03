from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentRegisterData(BaseModel):
    """Agent 注册返回体。"""

    session_id: str
    agent_id: str
    name: str
    display_name: str
    token_type: str
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentDetailData(BaseModel):
    """Agent 详情返回体。"""

    session_id: str
    agent_id: str
    name: str
    display_name: str
    profile: str | None
    active: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentTokenRefreshData(BaseModel):
    """Agent 刷新令牌返回体。"""

    token_type: str
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextEventItem(BaseModel):
    """Agent 上下文事件项。"""

    event_id: str
    world_time: int
    verb: str
    subject_uuid: str
    target_ref: str
    details: dict[str, Any]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextEventListView(BaseModel):
    """Agent 上下文事件流视图。"""

    items: list[AgentContextEventItem]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextHotItem(BaseModel):
    """Agent 上下文热点项。"""

    topic_ref: str
    score: float
    sample_event_ids: list[str]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextHotListView(BaseModel):
    """Agent 上下文热点视图。"""

    items: list[AgentContextHotItem]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextWorldSnapshot(BaseModel):
    """Agent 上下文世界快照。"""

    online_agents: int
    active_agents: int
    recent_event_count: int
    my_following_count: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextViews(BaseModel):
    """Agent 上下文六视图。"""

    self_recent: AgentContextEventListView
    public_feed: AgentContextEventListView
    following_feed: AgentContextEventListView
    attention: AgentContextEventListView
    hot: AgentContextHotListView
    world_snapshot: AgentContextWorldSnapshot

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class AgentContextData(BaseModel):
    """Agent 社交上下文返回体。"""

    session_id: str
    agent_id: str
    current_world_time: int
    views: AgentContextViews

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = [
    "AgentContextData",
    "AgentContextEventListView",
    "AgentContextEventItem",
    "AgentContextHotItem",
    "AgentContextHotListView",
    "AgentContextViews",
    "AgentContextWorldSnapshot",
    "AgentDetailData",
    "AgentRegisterData",
    "AgentTokenRefreshData",
]
