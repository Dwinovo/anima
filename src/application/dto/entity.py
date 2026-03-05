from __future__ import annotations

from dataclasses import dataclass

from src.application.dto.event import EventSearchItem


@dataclass(slots=True)
class EntityLifecycleResult:
    """Entity 生命周期操作结果 DTO。"""

    session_id: str
    entity_id: str
    active: bool
    name: str | None = None
    display_name: str | None = None
    source: str | None = None
    token_type: str | None = None
    access_token: str | None = None
    access_token_expires_in: int | None = None
    refresh_token: str | None = None
    refresh_token_expires_in: int | None = None


@dataclass(slots=True)
class EntityContextEventListView:
    """Entity 上下文事件流视图 DTO。"""

    items: list[EventSearchItem]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class EntityContextHotTopic:
    """Entity 上下文热点项 DTO。"""

    topic_ref: str
    score: float
    sample_event_ids: list[str]


@dataclass(slots=True)
class EntityContextHotListView:
    """Entity 上下文热点视图 DTO。"""

    items: list[EntityContextHotTopic]
    next_cursor: str | None
    has_more: bool


@dataclass(slots=True)
class EntityContextWorldSnapshot:
    """Entity 上下文世界快照 DTO。"""

    online_entities: int
    active_entities: int
    recent_event_count: int
    my_following_count: int


@dataclass(slots=True)
class EntityContextViews:
    """Entity 上下文六视图 DTO。"""

    self_recent: EntityContextEventListView
    public_feed: EntityContextEventListView
    following_feed: EntityContextEventListView
    attention: EntityContextEventListView
    hot: EntityContextHotListView
    world_snapshot: EntityContextWorldSnapshot


@dataclass(slots=True)
class EntityContextResult:
    """Entity 社交上下文结果 DTO。"""

    session_id: str
    entity_id: str
    current_world_time: int
    views: EntityContextViews


__all__ = [
    "EntityContextEventListView",
    "EntityContextHotListView",
    "EntityContextHotTopic",
    "EntityContextResult",
    "EntityContextViews",
    "EntityContextWorldSnapshot",
    "EntityLifecycleResult",
]
