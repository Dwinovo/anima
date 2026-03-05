from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class EntityRegisterData(BaseModel):
    """Entity 注册返回体。"""

    session_id: str
    entity_id: str
    name: str
    display_name: str
    source: str
    token_type: str
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityDetailData(BaseModel):
    """Entity 详情返回体。"""

    session_id: str
    entity_id: str
    name: str
    display_name: str
    source: str | None
    active: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityTokenRefreshData(BaseModel):
    """Entity 刷新令牌返回体。"""

    token_type: str
    access_token: str
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextEventItem(BaseModel):
    """Entity 上下文事件项。"""

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


class EntityContextEventListView(BaseModel):
    """Entity 上下文事件流视图。"""

    items: list[EntityContextEventItem]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextHotItem(BaseModel):
    """Entity 上下文热点项。"""

    topic_ref: str
    score: float
    sample_event_ids: list[str]

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextHotListView(BaseModel):
    """Entity 上下文热点视图。"""

    items: list[EntityContextHotItem]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextWorldSnapshot(BaseModel):
    """Entity 上下文世界快照。"""

    online_entities: int
    active_entities: int
    recent_event_count: int
    my_following_count: int

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextViews(BaseModel):
    """Entity 上下文六视图。"""

    self_recent: EntityContextEventListView
    public_feed: EntityContextEventListView
    following_feed: EntityContextEventListView
    attention: EntityContextEventListView
    hot: EntityContextHotListView
    world_snapshot: EntityContextWorldSnapshot

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EntityContextData(BaseModel):
    """Entity 社交上下文返回体。"""

    session_id: str
    entity_id: str
    current_world_time: int
    views: EntityContextViews

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = [
    "EntityContextData",
    "EntityContextEventListView",
    "EntityContextEventItem",
    "EntityContextHotItem",
    "EntityContextHotListView",
    "EntityContextViews",
    "EntityContextWorldSnapshot",
    "EntityDetailData",
    "EntityRegisterData",
    "EntityTokenRefreshData",
]
