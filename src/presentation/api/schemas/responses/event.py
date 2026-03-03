from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class EventReportData(BaseModel):
    """Event 上报成功后的响应体。"""

    session_id: str
    event_id: str
    world_time: int
    verb: str
    accepted: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EventListItem(BaseModel):
    """Event 列表单项响应体。"""

    event_id: str
    world_time: int
    verb: str
    subject_uuid: str
    target_ref: str
    details: dict[str, Any]
    schema_version: int
    is_social: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class EventListData(BaseModel):
    """Event 列表响应体。"""

    items: list[EventListItem]
    next_cursor: str | None
    has_more: bool

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


__all__ = ["EventReportData", "EventListItem", "EventListData"]
