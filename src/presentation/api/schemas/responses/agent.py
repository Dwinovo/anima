from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentRegisterData(BaseModel):
    """Agent 注册返回体。"""

    session_id: str
    agent_id: str
    name: str
    display_name: str

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


class AgentContextData(BaseModel):
    """Agent 社交上下文返回体。"""

    session_id: str
    agent_id: str
    status_events: list[AgentContextEventItem]
    media_events: list[AgentContextEventItem]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = [
    "AgentContextData",
    "AgentContextEventItem",
    "AgentDetailData",
    "AgentRegisterData",
]
