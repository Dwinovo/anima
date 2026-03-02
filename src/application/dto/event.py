from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EventReportResult:
    """事件上报结果 DTO。"""

    session_id: str
    event_id: str
    world_time: int
    verb: str
    accepted: bool


@dataclass(slots=True)
class EventSearchItem:
    """事件检索单项 DTO。"""

    event_id: str
    world_time: int
    verb: str
    subject_uuid: str
    target_ref: str
    details: dict[str, Any]
    schema_version: int
    is_social: bool


@dataclass(slots=True)
class EventSearchResult:
    """事件检索结果 DTO。"""

    session_id: str
    items: list[EventSearchItem]
    total: int


__all__ = ["EventReportResult", "EventSearchItem", "EventSearchResult"]
